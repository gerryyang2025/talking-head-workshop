"""Measure inner-lip separation on consecutive frames of a constant-rate studio export."""

import argparse
from pathlib import Path

import cv2 as cv

from studio.engine import FaceLandmarks
from studio.mouth_rest import mouth_geometry


def measure(path, first, stop, crop, tracker):
    cap = cv.VideoCapture(str(path))
    try:
        fps = cap.get(cv.CAP_PROP_FPS)
        if not cap.isOpened() or fps <= 0:
            raise ValueError(f"无法打开视频或读取帧率：{path}")
        if stop > int(cap.get(cv.CAP_PROP_FRAME_COUNT)):
            raise ValueError(f"区间超出视频帧数：{path}")
        width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        x, y, w, h = crop or (0, 0, width, height)
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
            raise ValueError(f"裁切区域超出 {width} × {height} 画面：{path}")

        cap.set(cv.CAP_PROP_POS_FRAMES, first)
        print(f"\n{path} · {fps:g} fps\n帧号\t秒\t唇间距 / 嘴宽")
        previous = peak = None
        for index in range(first, stop):
            ok, frame = cap.read()
            if not ok:
                raise ValueError(f"第 {index} 帧解码失败：{path}")
            try:
                points = tracker.landmarks(frame[y:y+h, x:x+w])
                geometry = mouth_geometry(points)
            except ValueError:
                geometry = None
            if geometry is None:
                print(f"{index}\t{index/fps:.3f}\t未测得")
                previous = None
                continue
            gap = geometry[0]
            print(f"{index}\t{index/fps:.3f}\t{gap:.2%}")
            if previous is not None:
                change = abs(gap - previous)
                if peak is None or change > peak[0]:
                    peak = (change, index)
            previous = gap
        if peak is None:
            raise ValueError(f"区间内未测得连续两帧的唇间距：{path}")
        change, end = peak
        print(f"最大单帧变化为嘴宽的 {change:.2%}，位于 {(end-1)/fps:.3f}–{end/fps:.3f} 秒")
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", type=Path, nargs="+", metavar="VIDEO")
    parser.add_argument("--first", type=int, required=True, help="首帧（从 0 开始，含）")
    parser.add_argument("--stop", type=int, required=True, help="结束帧（不含）")
    parser.add_argument("--crop", nargs=4, type=int, metavar=("X", "Y", "W", "H"),
                        help="主讲区域的像素坐标，默认整帧")
    args = parser.parse_args()
    if args.first < 0 or args.stop - args.first < 2:
        parser.error("请选择至少两帧，首帧从 0 开始")
    tracker = FaceLandmarks()
    for video in args.videos:
        try:
            measure(video, args.first, args.stop, args.crop, tracker)
        except ValueError as exc:
            parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
