
import argparse
import yaml

from dataloader import HighDTransfer, InDTransfer, NGSIMTransfer


def parameters():

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='highD')
    parser.add_argument('--data_folder', type=str, default='./original_data')
    parser.add_argument('--save_folder', type=str, default='./processed_data')
    parser.add_argument('--use_yml', type=str, default='./config/config.yaml')

    args = parser.parse_args()

    with open(args.use_yml, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    args.__dict__.update(config)
    return args

def get_driver(args):
    dataset = args.dataset.lower()
    if dataset == "highd":
        return HighDTransfer(args)
    if dataset == "ind":
        return InDTransfer(args)
    if dataset == "ngsim":
        return NGSIMTransfer(args)
    if dataset == "citysim":
        raise NotImplementedError("CitySimTransfer is not implemented yet.")
    raise ValueError(f"Unsupported dataset: {args.dataset}")

def main():
    args = parameters()
    transfer = get_driver(args)
    transfer.run()
    pass
