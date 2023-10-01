import configargparse
import importlib.util
import os
from typing import List, Dict, Any
from omegaconf import OmegaConf
import pprint
import glob


def config_parser(cmd=None, mode='config'):
    parser = configargparse.ArgumentParser()
    parser.add_argument('--config_init', type=str, help='config init file path')
    parser.add_argument('--config', type=str, help='config file path')
    parser.add_argument("--expname", type=str,
                        help='experiment name')
    parser.add_argument("--basedir", type=str, default='./log',
                        help='where to store ckpts and logs')
    parser.add_argument("--add_timestamp", type=int, default=0,
                        help='add timestamp to dir')
    parser.add_argument("--datadir", type=str, default='./data/nerf_synthetic/lego',
                        help='input data directory')
    parser.add_argument("--data_name", type=str, default=None)
    parser.add_argument("--progress_refresh_rate", type=int, default=10,
                        help='how many iterations to show psnrs or iters')

    parser.add_argument('--with_depth', action='store_true')
    parser.add_argument('--downsample_train', type=float, default=1.0)
    parser.add_argument('--downsample_test', type=float, default=1.0)

    parser.add_argument('--model_name', type=str, default='TensorVMSplitRBF')

    # loader options
    parser.add_argument("--batch_size", type=int, default=4096)
    parser.add_argument("--batch_size_init", type=int, default=None)
    parser.add_argument("--n_iters", type=int, default=30000)

    parser.add_argument('--dataset_name', type=str, default='blender')


    # training options
    # learning rate
    parser.add_argument("--lr_init", type=float, default=0.02,
                        help='learning rate')
    parser.add_argument("--lr_basis", type=float, default=1e-3,
                        help='learning rate')
    parser.add_argument("--lr_decay_iters", type=int, default=-1,
                        help = 'number of iterations the lr will decay to the target ratio; -1 will set it to n_iters')
    parser.add_argument("--lr_decay_target_ratio", type=float, default=0.1,
                        help='the target decay ratio; after decay_iters inital lr decays to lr*ratio')
    parser.add_argument("--lr_upsample_reset", type=int, default=1,
                        help='reset lr to inital after upsampling')

    # loss
    parser.add_argument("--L1_weight_inital", type=float, default=0.0,
                        help='loss weight')
    parser.add_argument("--L1_weight_rest", type=float, default=0,
                        help='loss weight')
    parser.add_argument("--Ortho_weight", type=float, default=0.0,
                        help='loss weight')
    parser.add_argument("--TV_weight_density", type=float, default=0.0,
                        help='loss weight')
    parser.add_argument("--TV_weight_app", type=float, default=0.0,
                        help='loss weight')

    # model
    # volume options
    parser.add_argument("--n_lamb_sigma", type=int, action="append")
    parser.add_argument("--n_lamb_sh", type=int, action="append")
    parser.add_argument("--data_dim_color", type=int, default=27)

    parser.add_argument("--rm_weight_mask_thre", type=float, default=0.0001,
                        help='mask points in ray marching')
    parser.add_argument("--alpha_mask_thre", type=float, default=0.0001,
                        help='threshold for creating alpha mask volume')
    parser.add_argument("--distance_scale", type=float, default=25,
                        help='scaling sampling distance for computation')
    parser.add_argument("--density_shift", type=float, default=-10,
                        help='shift density in softplus; making density = 0  when feature == 0')

    # network decoder
    parser.add_argument("--shadingMode", type=str, default="MLP_PE",
                        help='which shading mode to use')
    parser.add_argument("--pos_pe", type=int, default=6,
                        help='number of pe for pos')
    parser.add_argument("--view_pe", type=int, default=6,
                        help='number of pe for view')
    parser.add_argument("--fea_pe", type=int, default=6,
                        help='number of pe for features')
    parser.add_argument("--featureC", type=int, default=128,
                        help='hidden feature channel in MLP')



    parser.add_argument("--ckpt", type=str, default=None,
                        help='specific weights npy file to reload for coarse network')
    parser.add_argument("--render_only", type=int, default=0)
    parser.add_argument("--render_test", type=int, default=0)
    parser.add_argument("--render_train", type=int, default=0)
    parser.add_argument("--render_path", type=int, default=0)
    parser.add_argument("--export_mesh", type=int, default=0)

    # rendering options
    parser.add_argument('--lindisp', default=False, action="store_true",
                        help='use disparity depth sampling')
    parser.add_argument("--perturb", type=float, default=1.,
                        help='set to 0. for no jitter, 1. for jitter')
    parser.add_argument("--accumulate_decay", type=float, default=0.998)
    parser.add_argument("--fea2denseAct", type=str, default='softplus')
    parser.add_argument('--ndc_ray', type=int, default=0)
    parser.add_argument('--nSamples', type=int, default=1e6,
                        help='sample point each ray, pass 1e6 if automatic adjust')
    parser.add_argument('--step_ratio',type=float,default=0.5)


    ## blender flags
    parser.add_argument("--white_bkgd", action='store_true',
                        help='set to render synthetic data on a white bkgd (always use for dvoxels)')



    parser.add_argument('--N_voxel_init',
                        type=int,
                        default=100**3)
    parser.add_argument('--N_voxel_final',
                        type=int,
                        default=300**3)
    parser.add_argument("--upsamp_list", type=int, action="append")
    parser.add_argument("--update_AlphaMask_list", type=int, action="append")

    parser.add_argument('--idx_view',
                        type=int,
                        default=0)
    # logging/saving options
    parser.add_argument("--N_vis", type=int, default=5,
                        help='N images to vis')
    parser.add_argument("--vis_every", type=int, default=10000,
                        help='frequency of visualize the image')
    
    if cmd is not None:
        args = parser.parse_args(cmd)
    else:
        args = parser.parse_args()
    args = OmegaConf.create(vars(args))

    # Import config
    if mode == 'config_init':
        args.config = args.config_init
    if args.config is not None:
        spec = importlib.util.spec_from_file_location(os.path.basename(args.config), args.config)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)
        config = OmegaConf.create(cfg.config)

        # Override from config into argparse
        for k, v in config.items():
            # Keep certain args if they are set in cli
            if k in ['data_name', 'batch_size_init'] and getattr(args, k) is not None:
                continue
            setattr(args, k, v)

        # Replace placeholders with actual value
        args['datadir'] = args['datadir'].replace('data_name', args['data_name'])
        args['expname'] = args['expname'].replace('data_name', args['data_name'])
        if 'rbf_config' in args:
            if 'init_data_fp' in args['rbf_config']:
                args['rbf_config']['init_data_fp'] = args['rbf_config']['init_data_fp'].replace('data_name', args['data_name'])

    # Add version id
    if args.add_version_id:
        exp_list = glob.glob(f'{args["basedir"]}/{args["expname"]}-v*'.replace('[', '[[]'))
        if len(exp_list) == 0:
            vid = 0
        else:
            vid = max([int(v.split(f'{args["expname"]}-v')[-1]) for v in exp_list]) + 1
        args["expname"] += f'-v{vid}'

    return args
