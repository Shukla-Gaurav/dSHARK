import sys
from model_wrappers import (
    get_vae_mlir,
    get_unet_mlir,
    get_clip_mlir,
)
from stable_args import args
from utils import get_shark_model
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
if (
    args.precision != "fp16"
    or args.variant != "stablediffusion"
    or "rdna3" not in args.iree_vulkan_target_triple
):
    args.use_tuned = False
if args.use_tuned:
    print("Using tuned models for rdna3 card")


def get_unet():
    iree_flags = []
    if len(args.iree_vulkan_target_triple) > 0:
        iree_flags.append(
            f"-iree-vulkan-target-triple={args.iree_vulkan_target_triple}"
        )
    # Disable bindings fusion to work with moltenVK.
    if sys.platform == "darwin":
        iree_flags.append("-iree-stream-fuse-binding=false")

    if args.variant == "stablediffusion":
        # Tuned model is present for `fp16` precision.
        if args.precision == "fp16":
            if args.use_tuned:
                bucket = "gs://shark_tank/vivian"
                if args.version == "v1.4":
                    model_name = "unet_1dec_fp16_tuned"
                if args.version == "v2.1base":
                    if args.max_length == 64:
                        model_name = "unet_19dec_v2p1base_fp16_64_tuned"
                    else:
                        model_name = "unet2base_8dec_fp16_tuned_v2"
                return get_shark_model(bucket, model_name, iree_flags)
            else:
                bucket = "gs://shark_tank/stable_diffusion"
                model_name = "unet_8dec_fp16"
                if args.version == "v2.1base":
                    if args.max_length == 64:
                        model_name = "unet_19dec_v2p1base_fp16_64"
                    else:
                        model_name = "unet2base_8dec_fp16"
                if args.version == "v2.1":
                    model_name = "unet2_14dec_fp16"
                iree_flags += [
                    "--iree-flow-enable-padding-linalg-ops",
                    "--iree-flow-linalg-ops-padding-size=32",
                    "--iree-flow-enable-conv-img2col-transform",
                ]
                if args.import_mlir:
                    return get_unet_mlir(model_name, iree_flags)
                return get_shark_model(bucket, model_name, iree_flags)

        # Tuned model is not present for `fp32` case.
        if args.precision == "fp32":
            bucket = "gs://shark_tank/stable_diffusion"
            model_name = "unet_1dec_fp32"
            iree_flags += [
                "--iree-flow-enable-conv-nchw-to-nhwc-transform",
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=16",
            ]
            if args.import_mlir:
                return get_unet_mlir(model_name, iree_flags)
            return get_shark_model(bucket, model_name, iree_flags)

        if args.precision == "int8":
            bucket = "gs://shark_tank/prashant_nod"
            model_name = "unet_int8"
            iree_flags += [
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=32",
            ]
            sys.exit("int8 model is currently in maintenance.")
            # # TODO: Pass iree_flags to the exported model.
            # if args.import_mlir:
            # sys.exit(
            # "--import_mlir is not supported for the int8 model, try --no-import_mlir flag."
            # )
            # return get_shark_model(bucket, model_name, iree_flags)

    else:
        iree_flags += [
            "--iree-flow-enable-padding-linalg-ops",
            "--iree-flow-linalg-ops-padding-size=32",
            "--iree-flow-enable-conv-img2col-transform",
        ]
        if args.variant == "anythingv3":
            bucket = "gs://shark_tank/sd_anythingv3"
            model_name = f"av3_unet_19dec_{args.precision}"
        elif args.variant == "analogdiffusion":
            bucket = "gs://shark_tank/sd_analog_diffusion"
            model_name = f"ad_unet_19dec_{args.precision}"
        else:
            sys.exit(f"{args.variant} variant of SD is currently unsupported")

        if args.import_mlir:
            return get_unet_mlir(model_name, iree_flags)
        return get_shark_model(bucket, model_name, iree_flags)


def get_vae():
    iree_flags = []
    if len(args.iree_vulkan_target_triple) > 0:
        iree_flags.append(
            f"-iree-vulkan-target-triple={args.iree_vulkan_target_triple}"
        )
    # Disable bindings fusion to work with moltenVK.
    if sys.platform == "darwin":
        iree_flags.append("-iree-stream-fuse-binding=false")

    if args.variant == "stablediffusion":
        if args.precision in ["fp16", "int8"]:
            if args.use_tuned:
                bucket = "gs://shark_tank/vivian"
                if args.version == "v2.1base":
                    model_name = "vae2base_19dec_fp16_tuned"
                iree_flags += [
                    "--iree-flow-enable-padding-linalg-ops",
                    "--iree-flow-linalg-ops-padding-size=32",
                    "--iree-flow-enable-conv-img2col-transform",
                    "--iree-flow-enable-conv-winograd-transform",
                ]
                return get_shark_model(bucket, model_name, iree_flags)
            else:
                bucket = "gs://shark_tank/stable_diffusion"
                model_name = "vae_19dec_fp16"
                if args.version == "v2.1base":
                    model_name = "vae2base_19dec_fp16"
                if args.version == "v2.1":
                    model_name = "vae2_19dec_fp16"
                iree_flags += [
                    "--iree-flow-enable-padding-linalg-ops",
                    "--iree-flow-linalg-ops-padding-size=32",
                    "--iree-flow-enable-conv-img2col-transform",
                ]
                if args.import_mlir:
                    return get_vae_mlir(model_name, iree_flags)
                return get_shark_model(bucket, model_name, iree_flags)

        if args.precision == "fp32":
            bucket = "gs://shark_tank/stable_diffusion"
            model_name = "vae_1dec_fp32"
            iree_flags += [
                "--iree-flow-enable-conv-nchw-to-nhwc-transform",
                "--iree-flow-enable-padding-linalg-ops",
                "--iree-flow-linalg-ops-padding-size=16",
            ]
            if args.import_mlir:
                return get_vae_mlir(model_name, iree_flags)
            return get_shark_model(bucket, model_name, iree_flags)

    else:
        iree_flags += [
            "--iree-flow-enable-padding-linalg-ops",
        ]
        if args.precision == "fp16":
            iree_flags += [
                "--iree-flow-linalg-ops-padding-size=16",
                "--iree-flow-enable-conv-img2col-transform",
            ]
        elif args.precision == "fp32":
            iree_flags += [
                "--iree-flow-linalg-ops-padding-size=32",
                "--iree-flow-enable-conv-nchw-to-nhwc-transform",
            ]
        else:
            sys.exit("int8 precision is currently in not supported.")

        if args.variant == "anythingv3":
            bucket = "gs://shark_tank/sd_anythingv3"
            model_name = f"av3_vae_19dec_{args.precision}"

        elif args.variant == "analogdiffusion":
            bucket = "gs://shark_tank/sd_analog_diffusion"
            model_name = f"ad_vae_19dec_{args.precision}"

        else:
            sys.exit(f"{args.variant} variant of SD is currently unsupported")

        if args.import_mlir:
            return get_unet_mlir(model_name, iree_flags)
        return get_shark_model(bucket, model_name, iree_flags)


def get_clip():
    iree_flags = []
    if len(args.iree_vulkan_target_triple) > 0:
        iree_flags.append(
            f"-iree-vulkan-target-triple={args.iree_vulkan_target_triple}"
        )
    # Disable bindings fusion to work with moltenVK.
    if sys.platform == "darwin":
        iree_flags.append("-iree-stream-fuse-binding=false")

    if args.variant == "stablediffusion":
        bucket = "gs://shark_tank/stable_diffusion"
        model_name = "clip_18dec_fp32"
        if args.version == "v2.1base":
            if args.max_length == 64:
                model_name = "clip_19dec_v2p1base_fp32_64"
            else:
                model_name = "clip2base_18dec_fp32"
        if args.version == "v2.1":
            model_name = "clip2_18dec_fp32"
        iree_flags += [
            "--iree-flow-linalg-ops-padding-size=16",
            "--iree-flow-enable-padding-linalg-ops",
        ]
        if args.import_mlir:
            return get_clip_mlir(model_name, iree_flags)
        return get_shark_model(bucket, model_name, iree_flags)

    if args.variant == "anythingv3":
        bucket = "gs://shark_tank/sd_anythingv3"
        model_name = "av3_clip_19dec_fp32"
    elif args.variant == "analogdiffusion":
        bucket = "gs://shark_tank/sd_analog_diffusion"
        model_name = "ad_clip_19dec_fp32"
        iree_flags += [
            "--iree-flow-enable-padding-linalg-ops",
            "--iree-flow-linalg-ops-padding-size=16",
            "--iree-flow-enable-conv-img2col-transform",
        ]
    else:
        sys.exit(f"{args.variant} variant of SD is currently unsupported")

    if args.import_mlir:
        return get_unet_mlir(model_name, iree_flags)
    return get_shark_model(bucket, model_name, iree_flags)
