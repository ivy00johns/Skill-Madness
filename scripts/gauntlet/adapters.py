#!/usr/bin/env python3
"""Offline-only adapters for recorded engine events. No subprocesses or model calls.

Claude Code's coarse skill-usage hook is deliberately unsupported: it lacks
candidate content, terminal status and complete negative-trial evidence.
"""
import json


def normalize(protocol, raw, case, manifest, error_type):
    if protocol not in {'freebuff-sdk', 'hermes-stream'} or not isinstance(raw, list) or not raw:
        raise error_type('unsupported/empty host protocol; coarse hook logs are not proof')
    allowed_hosts = {'freebuff-sdk': {'freebuff', 'codebuff'}, 'hermes-stream': {'hermes'}}
    if manifest['binding']['host'] not in allowed_hosts[protocol]:
        raise error_type('native protocol does not match the observed host binding')
    if any(not isinstance(event, dict) for event in raw):
        raise error_type('native events must be objects')
    init = [e for e in raw if e.get('type') == ('init' if protocol == 'freebuff-sdk' else 'system')
            and (protocol == 'freebuff-sdk' or e.get('subtype') == 'init')]
    terminal = [e for e in raw if e.get('type') == 'result']
    if len(init) != 1 or raw[0] != init[0] or len(terminal) != 1 or raw[-1] != terminal[0]:
        raise error_type('native stream requires one leading init and terminal result')
    if init[0].get('model') != manifest['binding']['model']:
        raise error_type('native worker model missing/changed')
    if init[0].get('query') != case['query'] or init[0].get('mode') != case['mode']:
        raise error_type('native observer must record the actual dispatched query and invocation mode')
    tools = init[0].get('tools')
    native_tool = 'skill' if protocol == 'freebuff-sdk' else 'skill_view'
    if (not isinstance(tools, list) or native_tool not in tools
            or any(not isinstance(t, str) or not t for t in tools)
            or len(set(tools)) != len(tools)):
        raise error_type('native init must disclose the complete tool list')
    # Dispatch and user-origin calls need a separate trusted observer packet.
    # Never reinterpret engine model-origin calls as user invocation or dispatch.
    normalized_tools = ['skill' if t == native_tool else t for t in tools]
    events = [{'type': 'init', 'query': case['query'], 'mode': case['mode'], 'tools': normalized_tools}]
    for event in raw[1:-1]:
        event_type = event.get('type')
        if event_type in {'text', 'text_delta'}:
            text = event.get('text', event.get('delta', ''))
            if not isinstance(text, str):
                raise error_type('invalid native text event')
            events.append({'type': 'text', 'text': text})
        elif event_type == 'error':
            events.append({'type': 'error', 'message': str(event.get('message') or 'native execution error')})
        elif event_type in {'tool_call', 'tool_use'}:
            tool = event.get('toolName') if protocol == 'freebuff-sdk' else event.get('name')
            # Without modeling another tool's side effects, its presence is an
            # unsupported capture, not a clean no-retrieval negative.
            if tool != native_tool:
                raise error_type('unsupported native tool call: ' + str(tool))
            args = event.get('input')
            if not isinstance(args, dict):
                raise error_type('native call input must be an object')
            call_id = event.get('toolCallId') if protocol == 'freebuff-sdk' else event.get('tool_call_id')
            events.append({'type': 'tool_call', 'call_id': call_id, 'tool': 'skill',
                           'skill': args.get('name'), 'origin': 'model'})
        elif event_type == 'tool_result':
            tool = event.get('toolName') if protocol == 'freebuff-sdk' else event.get('name')
            if tool != native_tool:
                raise error_type('unsupported native tool result')
            output = event.get('output')
            if protocol == 'freebuff-sdk':
                if not isinstance(output, list) or len(output) != 1 or not isinstance(output[0], dict):
                    raise error_type('malformed Freebuff result envelope')
                value = output[0].get('value')
            else:
                try:
                    value = json.loads(output) if isinstance(output, str) else output
                except json.JSONDecodeError as exc:
                    raise error_type('malformed Hermes result JSON') from exc
            if not isinstance(value, dict) or not isinstance(value.get('content'), str):
                raise error_type('native result has no verifiable candidate content')
            content = value['content']
            failed = event.get('is_error') or value.get('success') is False
            status = 'error' if failed else 'refused' if content.startswith('Error:') else 'success'
            call_id = event.get('toolCallId') if protocol == 'freebuff-sdk' else event.get('tool_call_id')
            events.append({'type': 'tool_result', 'call_id': call_id, 'tool': 'skill',
                           'skill': value.get('name'), 'status': status, 'content': content})
        else:
            raise error_type('unsupported native event: ' + str(event_type))
    final = terminal[0]
    if type(final.get('exit_code')) is not int:
        raise error_type('native terminal exit code missing')
    status = 'completed' if final['exit_code'] == 0 and not final.get('error') else 'error'
    events.append({'type': 'terminal', 'status': status})
    return events
