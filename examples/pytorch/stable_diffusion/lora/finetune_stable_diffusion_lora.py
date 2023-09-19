import os
import tempfile
from dataclasses import dataclass, field

import cv2
import torch

from modelscope import snapshot_download
from modelscope.metainfo import Trainers
from modelscope.models import Model
from modelscope import get_logger
from modelscope.msdatasets import MsDataset
from modelscope.pipelines import pipeline
from modelscope.trainers import build_trainer
from modelscope.trainers.training_args import TrainingArgs
from modelscope.utils.constant import Tasks, DownloadMode
from swift import LoRAConfig, SwiftModel, Swift

logger = get_logger()

# Load configuration file and dataset
@dataclass(init=False)
class StableDiffusionLoraArguments(TrainingArgs):
    prompt: str = field(
        default='dog', metadata={
            'help': 'The pipeline prompt.',
        })

    lora_rank: int = field(
        default=4,
        metadata={
            'help': 'The rank size of lora intermediate linear.',
        })

    lora_alpha: int = field(
        default=32,
        metadata={
            'help': 'The factor to add the lora weights',
        })
    
    lora_dropout: float = field(
        default=0.0,
        metadata={
            'help': 'The dropout rate of the lora module',
        })
    
    bias: str = field(
        default='none',
        metadata={
            'help': 'Bias type. Values ca be "none", "all" or "lora_only"',
        })


training_args = StableDiffusionLoraArguments(
    task='text-to-image-synthesis').parse_cli()
config, args = training_args.to_config()

if os.path.exists(args.train_dataset_name):
    # Load local dataset
    train_dataset = MsDataset.load(args.train_dataset_name)
    validation_dataset = MsDataset.load(args.train_dataset_name)
else:
    # Load online dataset
    train_dataset = MsDataset.load(
        args.train_dataset_name,
        split='train',
        download_mode=DownloadMode.FORCE_REDOWNLOAD)
    validation_dataset = MsDataset.load(
        args.train_dataset_name,
        split='validation',
        download_mode=DownloadMode.FORCE_REDOWNLOAD)

def cfg_modify_fn(cfg):
    cfg.train.lr_scheduler = {
        'type': 'LambdaLR',
        'lr_lambda': lambda _: 1,
        'last_epoch': -1
    }
    return cfg

# build models
model = Model.from_pretrained(
    training_args.model,
    revision=args.model_revision)
model_dir = snapshot_download("AI-ModelScope/stable-diffusion-v2-1")
lora_config = LoRAConfig(r=args.lora_rank,
                         lora_alpha=args.lora_alpha,
                         lora_dropout=args.lora_dropout,
                         bias=args.bias,
                         target_modules=['to_q', 'to_k', 'query', 'value'])
model.unet = Swift.prepare_model(model.unet, lora_config)

# build trainer and training
kwargs = dict(
    model=model,
    cfg_file=os.path.join(model_dir, 'configuration.json'),
    work_dir=training_args.work_dir,
    train_dataset=train_dataset,
    eval_dataset=validation_dataset,
    cfg_modify_fn=cfg_modify_fn)

trainer = build_trainer(name=Trainers.stable_diffusion, default_args=kwargs)
trainer.train()

# save models
model.unet.save_pretrained(os.path.join(training_args.work_dir, "unet"))
logger.info(f"model save pretrained {training_args.work_dir}")

# pipeline after training and save result
pipe = pipeline(task=Tasks.text_to_image_synthesis,
                model=training_args.model,
                model_revision=args.model_revision,
                swift_lora_dir=os.path.join(training_args.work_dir, "unet"))
for index in range(10):
    image = pipe({'text': args.prompt})
    cv2.imwrite(f'./lora_result_{index}.png', image['output_imgs'][0])