import sys
from models.stable_diffusion.model_wrappers import (
    get_base_vae_mlir,
    get_vae_mlir,
    get_unet_mlir,
    get_clip_mlir,
)
from models.stable_diffusion.resources import models_db
from models.stable_diffusion.stable_args import args
from models.stable_diffusion.utils import get_shark_model
from shark.iree_utils.vulkan_utils import (
    get_iree_vulkan_args,
    map_device_to_path,
)

BATCH_SIZE = len(args.prompts)
if BATCH_SIZE != 1:
    sys.exit("Only batch size 1 is supported.")

# set fully qualified device.
args.device = map_device_to_path(args.device)
if not args.iree_vulkan_target_triple:
    vulkan_flags = get_iree_vulkan_args(args.device)
    if vulkan_flags:
        args.iree_vulkan_target_triple = vulkan_flags[0].split("=", 1)[1]

# use tuned models only in the case of stablediffusion/fp16 and rdna3 cards.
args.use_tuned = False
if (
    args.precision == "fp16"
    and args.variant == "stablediffusion"
    and "rdna3" in args.iree_vulkan_target_triple
):
    args.use_tuned = True
if args.use_tuned:
    print("Using tuned models for rdna3 card")


def get_params(model_key):
    iree_flags = []
    if len(args.iree_vulkan_target_triple) > 0:
        iree_flags.append(
            f"-iree-vulkan-target-triple={args.iree_vulkan_target_triple}"
        )

    # Disable bindings fusion to work with moltenVK.
    if sys.platform == "darwin":
        iree_flags.append("-iree-stream-fuse-binding=false")

    try:
        model_name = models_db[model_key]
    except KeyError:
        raise Exception(f"{model_key} is not present in the models database")

    return model_name, iree_flags


def get_unet():
    # Tuned model is present only for `fp16` precision.
    is_tuned = "/tuned" if args.use_tuned else "/untuned"
    variant_version = args.variant
    model_key = f"{args.variant}/{args.version}/unet/{args.precision}/length_{args.max_length}{is_tuned}"
    model_name, iree_flags = get_params(model_key)
    if args.use_tuned:
        bucket = "gs://shark_tank/vivian"
        return get_shark_model(bucket, model_name, iree_flags)
    else:
        bucket = "gs://shark_tank/stable_diffusion"
        if args.variant == "anythingv3":
            bucket = "gs://shark_tank/sd_anythingv3"
        elif args.variant == "analogdiffusion":
            bucket = "gs://shark_tank/sd_analog_diffusion"
        if args.precision == "fp16":
            iree_flags += [
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=32",
                "--iree-flow-enable-conv-img2col-transform",
            ]
        elif args.precision == "fp32":
            iree_flags += [
                "--iree-flow-enable-conv-nchw-to-nhwc-transform",
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=16",
            ]
        if args.import_mlir:
            return get_unet_mlir(model_name, iree_flags)
        return get_shark_model(bucket, model_name, iree_flags)


def get_vae():
    # Tuned model is present only for `fp16` precision.
    is_tuned = "/tuned" if args.use_tuned else "/untuned"
    is_base = "/base" if args.use_base_vae else ""
    model_key = f"{args.variant}/{args.version}/vae/{args.precision}/length_77{is_tuned}{is_base}"
    model_name, iree_flags = get_params(model_key)
    if args.use_tuned:
        bucket = "gs://shark_tank/vivian"
        iree_flags += [
            "--iree-flow-enable-padding-linalg-ops",
            "--iree-flow-linalg-ops-padding-size=32",
            "--iree-flow-enable-conv-img2col-transform",
            "--iree-flow-enable-conv-winograd-transform",
        ]
        return get_shark_model(bucket, model_name, iree_flags)
    else:
        bucket = "gs://shark_tank/stable_diffusion"
        if args.variant == "anythingv3":
            bucket = "gs://shark_tank/sd_anythingv3"
        elif args.variant == "analogdiffusion":
            bucket = "gs://shark_tank/sd_analog_diffusion"
        if args.precision == "fp16":
            iree_flags += [
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=32",
                "--iree-flow-enable-conv-img2col-transform",
            ]
        elif args.precision == "fp32":
            iree_flags += [
                "--iree-flow-enable-conv-nchw-to-nhwc-transform",
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=16",
            ]
        if args.import_mlir:
            if args.use_base_vae:
                return get_base_vae_mlir(model_name, iree_flags)
            return get_vae_mlir(model_name, iree_flags)
        return get_shark_model(bucket, model_name, iree_flags)


def get_clip():
    model_key = f"{args.variant}/{args.version}/clip/fp32/length_{args.max_length}/untuned"
    model_name, iree_flags = get_params(model_key)
    bucket = "gs://shark_tank/stable_diffusion"
    if args.variant == "anythingv3":
        bucket = "gs://shark_tank/sd_anythingv3"
    elif args.variant == "analogdiffusion":
        bucket = "gs://shark_tank/sd_analog_diffusion"
    iree_flags += [
        "--iree-flow-linalg-ops-padding-size=16",
        "--iree-flow-enable-padding-linalg-ops",
    ]
    if args.import_mlir:
        return get_clip_mlir(model_name, iree_flags)
    return get_shark_model(bucket, model_name, iree_flags)
