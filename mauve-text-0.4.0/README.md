# MAUVE

This is a library built on PyTorch and HuggingFace Transformers to measure the gap between neural text and human text
with the MAUVE measure, 
introduced in [this NeurIPS 2021 paper](https://arxiv.org/pdf/2102.01454.pdf) (Outstanding Paper Award) and [this JMLR 2023 paper](https://arxiv.org/pdf/2212.14578.pdf).


MAUVE is a measure of the gap between neural text and human text. It is computed using the Kullback–Leibler (KL) divergences between the two text distributions in a quantized embedding space of a large language model. MAUVE can identify differences in quality arising from model sizes and decoding algorithms.

### [Documentation Link](https://krishnap25.github.io/mauve/)  [GitHub Link](https://github.com/krishnap25/mauve/)

### _MAUVE is also available via [HuggingFace Evaluate](https://huggingface.co/spaces/evaluate-metric/mauve)!_


**Features**:
- MAUVE with quantization using *k*-means. 
- Adaptive selection of *k*-means hyperparameters. 
- Compute MAUVE using pre-computed GPT-2 features (i.e., terminal hidden state), 
    or featurize raw text using HuggingFace transformers + PyTorch.
- Use with other modalities (e.g. images or audio) by directly passing in pre-computed feature embeddings to our API.

More details can be found in the [documentation](https://krishnap25.github.io/mauve).

## Installation

For a direct install, run this command from your terminal:
```
pip install mauve-text
``` 

## Citation
If you find this package useful, or you use it in your research, please cite the following papers:
```
@article{pillutla-etal:mauve:jmlr2023,
  title={{MAUVE Scores for Generative Models: Theory and Practice}},
  author={Pillutla, Krishna and Liu, Lang and Thickstun, John and Welleck, Sean and Swayamdipta, Swabha and Zellers, Rowan and Oh, Sewoong and Choi, Yejin and Harchaoui, Zaid},
  journal={JMLR},
  year={2023}
}

@inproceedings{pillutla-etal:mauve:neurips2021,
  title={MAUVE: Measuring the Gap Between Neural Text and Human Text using Divergence Frontiers},
  author={Pillutla, Krishna and Swayamdipta, Swabha and Zellers, Rowan and Thickstun, John and Welleck, Sean and Choi, Yejin and Harchaoui, Zaid},
  booktitle = {NeurIPS},
  year      = {2021}
}

@inproceedings{liu-etal:mauve-theory:neurips2021,
  title={{Divergence Frontiers for Generative Models: Sample Complexity, Quantization Effects, and Frontier Integrals}},
  author={Liu, Lang and Pillutla, Krishna and Welleck, Sean and Oh, Sewoong and Choi, Yejin and Harchaoui, Zaid},
  booktitle={NeurIPS},
  year={2021}
}

```
    
## Acknowledgements
This work was supported by NSF DMS-2134012, NSF CCF-2019844, NSF DMS-2023166, the DARPA MCS program through NIWC Pacific (N66001-19-2-4031), the CIFAR "Learning in Machines & Brains" program, a Qualcomm Innovation Fellowship, and faculty research awards.


