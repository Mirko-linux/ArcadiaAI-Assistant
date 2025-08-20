# export_phi2_onnx.py
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from onnx import save_model

model_name = "microsoft/phi-2"
output_dir = "assets/models"

# Carica modello e tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Esporta in ONNX
with torch.no_grad():
    dummy_input = tokenizer("Hello world", return_tensors="pt")
    torch.onnx.export(
        model,
        (dummy_input['input_ids'], dummy_input['attention_mask']),
        f"{output_dir}/phi2.onnx",
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input_ids', 'attention_mask'],
        output_names=['logits'],
        dynamic_axes={
            'input_ids': {0: 'batch', 1: 'sequence'},
            'attention_mask': {0: 'batch', 1: 'sequence'},
            'logits': {0: 'batch', 1: 'sequence'}
        },
        use_external_data_format=True
    )
print("✅ Modello esportato in ONNX!")