# Experimental environment: 3090
# 12GB GPU memory
CUDA_VISIBLE_DEVICES=0 \
python src/llm_sft.py \
    --model_type baichuan2-7b-chat \
    --sft_type lora \
    --template_type baichuan \
    --dtype bf16 \
    --output_dir output \
    --dataset advertise-gen \
    --train_dataset_sample -1 \
    --num_train_epochs 1 \
    --max_length 2048 \
    --quantization_bit 4 \
    --bnb_4bit_comp_dtype bf16 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --lora_dropout_p 0. \
    --lora_target_modules ALL \
    --gradient_checkpointing false \
    --batch_size 1 \
    --weight_decay 0. \
    --learning_rate 1e-4 \
    --gradient_accumulation_steps 16 \
    --max_grad_norm 0.5 \
    --warmup_ratio 0.03 \
    --eval_steps 100 \
    --save_steps 100 \
    --save_total_limit 2 \
    --logging_steps 10 \
    --push_to_hub false \
    --hub_model_id baichuan2-7b-chat-qlora \
    --hub_private_repo true \
    --hub_token 'your-sdk-token' \
