#!/usr/bin/python2
#
# Copyright 2020 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# gen_restricted_traces.py:
#   Generates integration code for the restricted trace tests.

import json
import sys

gni_template = """# GENERATED FILE - DO NOT EDIT.
# Generated by {script_name} using data from {data_source_name}
#
# Copyright 2020 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# A list of all restricted trace tests. Can be consumed by tests/BUILD.gn.

angle_restricted_traces = [
{test_list}
]
"""

header_template = """// GENERATED FILE - DO NOT EDIT.
// Generated by {script_name} using data from {data_source_name}
//
// Copyright 2020 The ANGLE Project Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
//
// Types and enumerations for trace tests.

#ifndef ANGLE_RESTRICTED_TRACES_H_
#define ANGLE_RESTRICTED_TRACES_H_

{includes}

namespace angle
{{
enum class RestrictedTraceID
{{
{trace_ids}, InvalidEnum, EnumCount = InvalidEnum
}};

using ReplayFunc = void (*)(uint32_t);
using SetupFunc = void (*)();
using DecompressFunc = uint8_t *(*)(const std::vector<uint8_t> &);
using SetBinaryDataDirFunc = void (*)(const char *);

static constexpr size_t kTraceInfoMaxNameLen = 32;

struct TraceInfo
{{
    uint32_t startFrame;
    uint32_t endFrame;
    char name[kTraceInfoMaxNameLen];
}};

constexpr angle::PackedEnumMap<RestrictedTraceID, TraceInfo> kTraceInfos = {{
{trace_infos}
}};

using DecompressCallback = uint8_t *(*)(const std::vector<uint8_t> &);
using FramebufferChangeCallback = void(*)(void *userData, GLenum target, GLuint framebuffer);

inline void ReplayFrame(RestrictedTraceID traceID, uint32_t frameIndex)
{{
    switch (traceID)
    {{
{replay_func_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

inline void SetupReplay(RestrictedTraceID traceID)
{{
    switch (traceID)
    {{
{setup_func_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

inline void SetBinaryDataDir(RestrictedTraceID traceID, const char *dataDir)
{{
    switch (traceID)
    {{
{set_binary_data_dir_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

inline void SetBinaryDataDecompressCallback(RestrictedTraceID traceID, DecompressCallback callback)
{{
    switch (traceID)
    {{
{decompress_callback_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}

inline void SetFramebufferChangeCallback(RestrictedTraceID traceID, void *userData, FramebufferChangeCallback callback)
{{
    switch (traceID)
    {{
{on_fb_change_callback_cases}
        default:
            fprintf(stderr, "Error in switch.\\n");
            assert(0);
            break;
    }}
}}
}}  // namespace angle

#endif  // ANGLE_RESTRICTED_TRACES_H_
"""


def reject_duplicate_keys(pairs):
    found_keys = {}
    for key, value in pairs:
        if key in found_keys:
            raise ValueError("duplicate key: %r" % (key,))
        else:
            found_keys[key] = value
    return found_keys


def gen_gni(traces, gni_file, format_args):
    format_args["test_list"] = ",\n".join(['"%s"' % trace for trace in traces])
    gni_data = gni_template.format(**format_args)
    with open(gni_file, "w") as out_file:
        out_file.write(gni_data)
    return True


def get_trace_info(trace):
    info = ["%s::kReplayFrameStart", "%s::kReplayFrameEnd", "\"%s\""]
    return ", ".join([element % trace for element in info])


def get_cases(traces, function, args):
    funcs = [
        "case RestrictedTraceID::%s: %s::%s(%s); break;" % (trace, trace, function, args)
        for trace in traces
    ]
    return "\n".join(funcs)


def gen_header(traces, header_file, format_args):

    includes = ["#include \"%s/%s_capture_context1.h\"" % (trace, trace) for trace in traces]
    trace_infos = [
        "{RestrictedTraceID::%s, {%s}}" % (trace, get_trace_info(trace)) for trace in traces
    ]

    format_args["includes"] = "\n".join(includes)
    format_args["trace_ids"] = ",\n".join(traces)
    format_args["trace_infos"] = ",\n".join(trace_infos)
    format_args["replay_func_cases"] = get_cases(traces, "ReplayContext1Frame", "frameIndex")
    format_args["setup_func_cases"] = get_cases(traces, "SetupContext1Replay", "")
    format_args["set_binary_data_dir_cases"] = get_cases(traces, "SetBinaryDataDir", "dataDir")
    format_args["decompress_callback_cases"] = get_cases(traces, "SetBinaryDataDecompressCallback",
                                                         "callback")
    format_args["on_fb_change_callback_cases"] = get_cases(traces, "SetFramebufferChangeCallback",
                                                           "userData, callback")
    header_data = header_template.format(**format_args)
    with open(header_file, "w") as out_file:
        out_file.write(header_data)
    return True


def read_json(json_file):
    with open(json_file) as map_file:
        return json.loads(map_file.read(), object_pairs_hook=reject_duplicate_keys)


def main():
    json_file = 'restricted_traces.json'
    gni_file = 'restricted_traces_autogen.gni'
    header_file = 'restricted_traces_autogen.h'

    # auto_script parameters.
    if len(sys.argv) > 1:
        inputs = [json_file]
        outputs = [gni_file, header_file]

        if sys.argv[1] == 'inputs':
            print ','.join(inputs)
        elif sys.argv[1] == 'outputs':
            print ','.join(outputs)
        else:
            print('Invalid script parameters.')
            return 1
        return 0

    json_data = read_json(json_file)
    if 'traces' not in json_data:
        print('Trace data missing traces key.')
        return 1

    format_args = {
        "script_name": __file__,
        "data_source_name": json_file,
    }

    traces = json_data['traces']
    if not gen_gni(traces, gni_file, format_args):
        print('.gni file generation failed.')
        return 1

    if not gen_header(traces, header_file, format_args):
        print('.h file generation failed.')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
