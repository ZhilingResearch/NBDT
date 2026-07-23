
import argparse
import yaml

from dataloader import HighDTransfer, InDTransfer, CitySimTransfer, NGSIMTransfer, WaymoTransfer, LyftTransfer
from openacc_transfer import OpenACCTransfer
from adas_one_transfer import ADASOneVehicleTransfer
from adas_two_transfer import ADASTwoVehicleTransfer


def parameters():

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='highD')
    parser.add_argument('--data_folder', type=str, default='./original_data')
    parser.add_argument('--save_folder', type=str, default='./processed_data')
    parser.add_argument('--use_yml', type=str, default=None)

    args = parser.parse_args()

    if args.use_yml is None:
        return args

    with open(args.use_yml, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    args.__dict__.update(config)
    return args

def get_driver(args):
    if args.dataset == "highD":
        return HighDTransfer(args)
    elif args.dataset == "inD":
        args.scale_down_factor = 12
        return InDTransfer(args)
    elif args.dataset == "rounD":
        args.scale_down_factor = 10
        return InDTransfer(args)
    elif args.dataset == "CitySim":
        return CitySimTransfer(args)
    elif args.dataset == "NGSIM":
        return NGSIMTransfer(args)
    elif args.dataset == "Waymo":
        return WaymoTransfer(args)
    elif args.dataset == "Lyft":
        return LyftTransfer(args)
    elif args.dataset == "OpenACC":
        return OpenACCTransfer(args)
    elif args.dataset == "ADAS_single":
        return ADASOneVehicleTransfer(args)
    elif args.dataset == "ADAS_two_vehicle":
        return ADASTwoVehicleTransfer(args)
    else:
        raise ValueError(f"Unknown dataset: {args.dataset}")

def main():
    args = parameters()
    transfer = get_driver(args)
    transfer.run()


if __name__ == "__main__":
    main()