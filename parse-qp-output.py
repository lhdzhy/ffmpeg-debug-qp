#!/usr/bin/env python3
#
# Author: Werner Robitza
#
# Parses output from ffmpeg-debug-qp script.
# Writes per-frame QP values in JSON format.

import os
import re
import argparse
import sys
import json
import numpy
import argparse
import math
import subprocess

# def parse_args():
#     parser = argparse.ArgumentParser(description='QECNN')
#     parser.add_argument('height', type=int,
#                         help='resolution_height')
#     parser.add_argument('width', type=int,
#                         help='resolution_width')
#
#     args = parser.parse_args()
#
#     return args


def parse_file(input_file, height, width):
    all_frame_data = []
    with open(input_file) as f:
        frame_index = -1
        frame_found = False
        for line in f:
            line = line.strip()
            # skip all non-relevant lines
            if "[h264" not in line and "pkt_size" not in line:
                continue
            # skip irrelevant other lines
            if "nal_unit_type" in line or "Reinit context" in line:
                continue
            # start a new frame
            if "New frame" in line:
                frame_found = True
                frame_type = line[-1]
                if frame_type not in ["I", "P", "B"]:
                    print("Wrong frame type parsed: " + str(frame_type))
                    sys.exit(1)
                frame_index += 1
                # print("Frame parsed, type " + frame_type + ", index: " + str(frame_index))
                all_frame_data.append({
                    "frameType": frame_type,
                    "qpValues": [],
                    "frameSize": 0,
                    "Avg_qp": 0
                })
                continue
            if frame_found and "[h264" in line and "pkt_size" not in line:

                if "Missing" in line or "missing" in line:
                    frame_index += 1
                    all_frame_data.append({
                    "frameType": frame_type,
                    "qpValues" : [],
                    "frameSize" : 0,
                    "Avg_qp" : 0
                    })
                    all_frame_data[frame_index] = all_frame_data[frame_index - 1]
                    print("missing\n")
                    continue
                    # missing frame

                if set(line.split("] ")[1]) - set("0123456789 ") != set():
                    # this line contains something that is not a qp value
                    continue
                # Now we have a line with qp values.
                # Strip the first part off the string, e.g.
                #   [h264 @ 0x7fadf2008000] 1111111111111111111111111111111111111111
                # becomes:
                #   1111111111111111111111111111111111111111
                raw_values = re.sub(r'\[[\w\s@]+\]\s', '', line)
                qp_values = [int(raw_values[i:i + 2])
                             for i in range(0, len(raw_values), 2)]
                # print("Adding QP values to frame with index " + str(frame_index))
                all_frame_data[frame_index]["qpValues"].extend(qp_values)
                continue
            if "pkt_size" in line:
                frame_size = re.findall(r'\d+', line)[0]
                all_frame_data[frame_index]["frameSize"] = frame_size
                height_mb = math.ceil(height / 16.0)
                width_mb = math.ceil(width / 16.0)

                # Avg_qp = int(sum(all_frame_data[frame_index]["qpValues"])/(120*68))
                Avg_qp = int(sum(all_frame_data[frame_index]["qpValues"])/(height_mb*width_mb))
                # FrameSize 1920 x 1080  MacroblockSize 16 x 16
                all_frame_data[frame_index]["Avg_qp"] = Avg_qp
                # calculate average QP of each frame

    file = open(input_file[:-4]+"QP.txt",'a')
    for index in range(frame_index+1):
        print(all_frame_data[index]["Avg_qp"])
        file.write("Index: %s ,AverageQP: %d\n"%(index,all_frame_data[index]["Avg_qp"]))
    file.close
    # output averageQP

    return all_frame_data


def main():

    parser = argparse.ArgumentParser(
        description="Parse QP values from ffmpeg-debug-qp")
    parser.add_argument("input", type=str, help="Input log file")
    parser.add_argument("output", type=str, help="Output JSON file")
    parser.add_argument("height", type=float, help="Input height")
    parser.add_argument("width", type=float, help="Input width")

    args = vars(parser.parse_args())
    if not os.path.isfile(args["input"]):
        print("no such file: " + args["input"])
        sys.exit(1)
    data = parse_file(args["input"], args["height"], args["width"])

    with open(args["output"], "w") as of:
        json.dump(data, of)

    cmd_remove_json = 'rm -rf ' + args["output"]
    subprocess.call(cmd_remove_json, shell=True)

if __name__ == '__main__':
    # args = parse_args()
    # height = args.height
    # width = args.width

    main()
