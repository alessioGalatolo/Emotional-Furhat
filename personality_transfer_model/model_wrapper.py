from importlib import import_module
import os.path as path
import texar.torch as tx
import torch
from ctrl_gen_model_torch import CtrlGenModel


class PersonalityTransfer:
    def __init__(self, config_module, device='cpu'):
        config = import_module(config_module)
        config = tx.HParams(config.tf_config2torch(config.model), None)
        checkpoint_path = path.join(config.checkpoint_path, 'final_model.pth')
        assert path.exists(checkpoint_path)

        checkpoint = torch.load(checkpoint_path)
        self.input_len = checkpoint['input_len']

        # FIXME: should not access that default hparams
        vocab_hp = tx.HParams({'vocab_file': checkpoint['vocab_file']},
                              tx.data.data.multi_aligned_data._default_dataset_hparams())
        self.vocab = tx.data.MultiAlignedData.make_vocab([vocab_hp])[0]
        self.model = CtrlGenModel(self.input_len,
                                  self.vocab, config, device)
        self.model.load_state_dict(checkpoint['model_state_dict'], strict=True)

    def transfer(self, text, transfer_clas):
        # FIXME what if the text is not in the vocab?
        # Eval
        text_tokens = text.split()
        text_tokens.insert(0, self.vocab.bos_token)
        text_tokens.append(self.vocab.eos_token)
        if len(text_tokens) < self.input_len:  # FIXME: check length and eventually pad sequence
            for _ in range(self.input_len-len(text_tokens)):
                text_tokens.append('')
        text_ids = self.vocab.map_tokens_to_ids_py(text_tokens)
        output_ids = self.model.infer(text_ids, transfer_clas)

        hyps = self.vocab.map_ids_to_tokens_py(output_ids)
        output_str = ' '.join(hyps.tolist())
        return output_str


# Testing
if __name__ == "__main__":
    personality_transfer = PersonalityTransfer('config')
    print(personality_transfer.transfer("this a not so long text", 0))