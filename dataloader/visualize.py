"""
Visualize processed NBDT bounding boxes on highD highway background images.
Usage:
    python dataloader/visualize.py                       # visualize all recordings
    python dataloader/visualize.py --recordings 1 7 25   # visualize specific recordings
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image


def visualize_recording(rec_id, original_folder, processed_folder, output_folder):
    """Overlay OBB bounding boxes on highway background image for one recording."""
    prefix = f"{rec_id:02d}"
    img_path = os.path.join(original_folder, f"{prefix}_highway.png")
    csv_path = os.path.join(processed_folder, f"{prefix}_tracks.csv")

    if not os.path.exists(img_path) or not os.path.exists(csv_path):
        print(f"  Skipping rec {prefix}: missing files")
        return

    img = Image.open(img_path)
    df = pd.read_csv(csv_path)

    # Pick the frame with the most vehicles
    frame_counts = df['frameNum'].value_counts()
    target_frame = frame_counts.idxmax()
    frame_data = df[df['frameNum'] == target_frame]

    fig, ax = plt.subplots(1, 1, figsize=(22, 4))
    ax.imshow(np.array(img), extent=[0, img.size[0], img.size[1], 0])

    # Draw each vehicle's OBB as a polygon (4 corners)
    for _, row in frame_data.iterrows():
        corners_x = [row['boundingBox1X'], row['boundingBox2X'],
                      row['boundingBox3X'], row['boundingBox4X']]
        corners_y = [row['boundingBox1Y'], row['boundingBox2Y'],
                      row['boundingBox3Y'], row['boundingBox4Y']]

        color = 'red' if row['objClass'] == 0 else 'blue'
        polygon = plt.Polygon(list(zip(corners_x, corners_y)),
                               closed=True, fill=False,
                               edgecolor=color, linewidth=1.5)
        ax.add_patch(polygon)

        # Draw center point
        ax.plot(row['carCenterX'], row['carCenterY'], '.', color=color, markersize=3)

    ax.set_xlim(0, img.size[0])
    ax.set_ylim(img.size[1], 0)
    ax.set_title(f"Recording {prefix}, Frame {target_frame}, "
                 f"{len(frame_data)} vehicles, img={img.size[0]}x{img.size[1]}")
    plt.tight_layout()

    save_path = os.path.join(output_folder, f"verify_{prefix}.png")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {save_path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize NBDT bounding boxes on highway images")
    parser.add_argument('--original_folder', type=str, default='./original_data')
    parser.add_argument('--processed_folder', type=str, default='./processed_data')
    parser.add_argument('--output_folder', type=str, default='./verify_output')
    parser.add_argument('--recordings', type=int, nargs='*', default=None,
                        help='Recording IDs to visualize (default: all 1-60)')
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    rec_ids = args.recordings if args.recordings else list(range(1, 61))
    print(f"Visualizing {len(rec_ids)} recording(s)...")

    for rec_id in rec_ids:
        visualize_recording(rec_id, args.original_folder,
                            args.processed_folder, args.output_folder)

    print("Done.")


if __name__ == '__main__':
    main()
