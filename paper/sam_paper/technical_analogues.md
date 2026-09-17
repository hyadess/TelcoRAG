# Technical analogues — the RAG, telecom and evaluation literature

**What this file is.** Twelve papers that are technically closest to what this repository does, all of them **openly available**, all downloaded to `pdfs/`. Metadata verified via OpenAlex on 2026-09-13; abstracts are reproduced verbatim from the same source.

**These are not models for how to write the T&I submission.** They are the technical foundation you cite, and they are what a knowledgeable reviewer will measure your novelty against. For how the *paper* should be written, see `journal_precedents.md`.

**Tiers.** TIER 1 = read in full. TIER 2 = read the method and evaluation sections. TIER 3 = cite and skim.

---

## Telco-RAG: Navigating the Challenges of Retrieval-Augmented Language Models for Telecommunications

**TIER 1 — nearest system** · file: [`pdfs/01_TelcoRAG_Bornea2024.pdf`](pdfs/01_TelcoRAG_Bornea2024.pdf)

| | |
| --- | --- |
| Authors | Andrei-Laurentiu Bornea, Fadhel Ayed, Antonio De Domenico, Nicola Piovesan, Ali Maatouk |
| Year | 2024 |
| Venue | arXiv:2404.15939. Also published at IEEE GLOBECOM 2024 (doi:10.1109/globecom52923.2024.10901158). The PDF here is the arXiv version. |
| DOI | [10.48550/arxiv.2404.15939](https://doi.org/10.48550/arxiv.2404.15939) |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** *(verbatim, via OpenAlex)*

> The application of Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) systems in the telecommunication domain presents unique challenges, primarily due to the complex nature of telecom standard documents and the rapid evolution of the field. The paper introduces Telco-RAG, an open-source RAG framework designed to handle the specific needs of telecommunications standards, particularly 3rd Generation Partnership Project (3GPP) documents. Telco-RAG addresses the critical challenges of implementing a RAG pipeline on highly technical content, paving the way for applying LLMs in telecommunications and offering guidelines for RAG implementation in other technical domains.

**Why it matters for us.** The closest published system to this project, and it shares the name. A RAG pipeline purpose-built for telecom technical standards (3GPP), with domain-specific tuning of chunk size, context length, embeddings and a query-augmentation step. **Read it first and be explicit in Related Work about what is different:** their corpus is international technical standards, yours is a national *regulatory and licensing* corpus; their evaluation is multiple-choice accuracy on TeleQnA, yours is expert judgement on open-ended answers about legal obligations. Positioning against this paper is mandatory — a reviewer who knows the area will ask.

**What to take from it.** The ablation discipline: one design decision at a time, each justified by a property of the corpus.

---

## TeleQnA: A Benchmark Dataset to Assess Large Language Models Telecommunications Knowledge

**TIER 1 — benchmark precedent** · file: [`pdfs/02_TeleQnA_Maatouk2023.pdf`](pdfs/02_TeleQnA_Maatouk2023.pdf)

| | |
| --- | --- |
| Authors | Ali Maatouk, Fadhel Ayed, Nicola Piovesan, Antonio De Domenico, Mérouane Debbah, Zhi‐Quan Luo |
| Year | 2023 |
| Venue | arXiv:2310.15051. Also published in IEEE Network, 2025 (doi:10.1109/mnet.2025.3576035). The PDF here is the arXiv version. |
| DOI | [10.48550/arxiv.2310.15051](https://doi.org/10.48550/arxiv.2310.15051) |
| Citations (OpenAlex, 2026-09-13) | 14 |

**Abstract** *(verbatim, via OpenAlex)*

> We introduce TeleQnA, the first benchmark dataset designed to evaluate the knowledge of Large Language Models (LLMs) in telecommunications. Comprising 10,000 questions and answers, this dataset draws from diverse sources, including standards and research articles. This paper outlines the automated question generation framework responsible for creating this dataset, along with how human input was integrated at various stages to ensure the quality of the questions. Afterwards, using the provided dataset, an evaluation is conducted to assess the capabilities of LLMs, including GPT-3.5 and GPT-4. The results highlight that these models struggle with complex standards related questions but exhibit proficiency in addressing general telecom-related inquiries. Additionally, our results showcase how incorporating telecom knowledge context significantly enhances their performance, thus shedding light on the need for a specialized telecom foundation model. Finally, the dataset is shared with active telecom professionals, whose performance is subsequently benchmarked against that of the LLMs. The findings illustrate that LLMs can rival the performance of active professionals in telecom knowledge, thanks to their capacity to process vast amounts of information, underscoring the potential of LLMs within this domain. The dataset has been made publicly accessible on GitHub.

**Why it matters for us.** The reference benchmark for telecom knowledge in LLMs, and the yardstick Telco-RAG uses. Important for you as a *contrast*: TeleQnA is multiple-choice over technical standards, which sidesteps every problem your evaluation has to face (open-ended generation, completeness, groundedness, abstention). Use it to argue why a new evaluation design is needed for regulatory QA.

**What to take from it.** The dataset-construction section: how questions were generated, filtered and validated. Your §7.3 query-set construction should be documented at this level of detail.

---

## RAGAs: Automated Evaluation of Retrieval Augmented Generation

**TIER 1 — the framework your judge implements** · file: [`pdfs/03_RAGAS_EsMagdy2024.pdf`](pdfs/03_RAGAS_EsMagdy2024.pdf)

| | |
| --- | --- |
| Authors | Shahul Es, Jithin James, Luis Espinosa-Anke, Steven Schockaert |
| Year | 2024 |
| Venue | EACL 2024, System Demonstrations (ACL Anthology 2024.eacl-demo.16). |
| DOI | [10.18653/v1/2024.eacl-demo.16](https://doi.org/10.18653/v1/2024.eacl-demo.16) |
| Citations (OpenAlex, 2026-09-13) | 444 |

**Abstract** *(verbatim, via OpenAlex)*

> Shahul Es, Jithin James, Luis Espinosa Anke, Steven Schockaert. Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations. 2024.

**Why it matters for us.** RAGAS defines the reference-free triad — faithfulness, answer relevance, context relevance — that your `evaluation/judge/` modules mirror. Cite it as the origin of your automatic metrics. The `answer_relevance` module in this repo describes itself as 'RAGAS-style' in its own docstring.

**What to take from it.** The precise definitions of each metric. Quote them when you define your automatic metrics, so the mapping table in guideline.md §8 rests on published definitions rather than local ones.

---

## ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems

**TIER 1 — automated RAG evaluation, and its validation problem** · file: [`pdfs/04_ARES_SaadFalcon2024.pdf`](pdfs/04_ARES_SaadFalcon2024.pdf)

| | |
| --- | --- |
| Authors | Jon Saad-Falcon, Omar Khattab, Christopher Potts, Matei Zaharia |
| Year | 2024 |
| Venue | NAACL 2024, Long Papers (ACL Anthology 2024.naacl-long.20). |
| DOI | [10.18653/v1/2024.naacl-long.20](https://doi.org/10.18653/v1/2024.naacl-long.20) |
| Citations (OpenAlex, 2026-09-13) | 123 |

**Abstract** *(verbatim, via OpenAlex)*

> Jon Saad-Falcon, Omar Khattab, Christopher Potts, Matei Zaharia. Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers). 2024.

**Why it matters for us.** ARES trains lightweight LLM judges and, crucially, uses prediction-powered inference with a small set of human annotations to give statistical guarantees. This is the most directly relevant prior work to your RQ2: it takes seriously that automated judges need human anchoring.

**What to take from it.** The argument for why human annotations remain necessary even in an 'automated' framework. This is the citation that justifies your whole study design.

---

## Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena

**TIER 1 — judge bias, already cited in your code** · file: [`pdfs/05_LLMasJudge_MTBench_Zheng2023.pdf`](pdfs/05_LLMasJudge_MTBench_Zheng2023.pdf)

| | |
| --- | --- |
| Authors | Zheng, Lianmin, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang et al. |
| Year | 2023 |
| Venue | arXiv:2306.05685. Also published in the NeurIPS 2023 Datasets and Benchmarks Track [verify the exact citation before use]. |
| DOI | [10.48550/arxiv.2306.05685](https://doi.org/10.48550/arxiv.2306.05685) |
| Citations (OpenAlex, 2026-09-13) | 485 |

**Abstract** *(verbatim, via OpenAlex)*

> Evaluating large language model (LLM) based chat assistants is challenging due to their broad capabilities and the inadequacy of existing benchmarks in measuring human preferences. To address this, we explore using strong LLMs as judges to evaluate these models on more open-ended questions. We examine the usage and limitations of LLM-as-a-judge, including position, verbosity, and self-enhancement biases, as well as limited reasoning ability, and propose solutions to mitigate some of them. We then verify the agreement between LLM judges and human preferences by introducing two benchmarks: MT-bench, a multi-turn question set; and Chatbot Arena, a crowdsourced battle platform. Our results reveal that strong LLM judges like GPT-4 can match both controlled and crowdsourced human preferences well, achieving over 80% agreement, the same level of agreement between humans. Hence, LLM-as-a-judge is a scalable and explainable way to approximate human preferences, which are otherwise very expensive to obtain. Additionally, we show our benchmark and traditional benchmarks complement each other by evaluating several variants of LLaMA and Vicuna. The MT-bench questions, 3K expert votes, and 30K conversations with human preferences are publicly available at https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge.

**Why it matters for us.** The canonical study of LLM-as-a-judge, including position bias, verbosity bias and self-enhancement bias, with agreement rates against human preference. **`evaluation/judge/modules/pairwise.py` already cites this paper in its docstring** as the reason for the position-swapped double pass. Cite it in the manuscript for the same reason, and again in Limitations for self-preference bias (guideline.md §9.1).

**What to take from it.** The human-agreement methodology, and how they report agreement rates as the headline number. Your Table 7 should be recognisable to anyone who has read this paper.

---

## Retrieval-Augmented Generation for Large Language Models: A Survey

**TIER 2 — survey, for Related Work scaffolding** · file: [`pdfs/06_RAG_Survey_Gao2023.pdf`](pdfs/06_RAG_Survey_Gao2023.pdf)

| | |
| --- | --- |
| Authors | Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi et al. |
| Year | 2023 |
| Venue | arXiv:2312.10997, revised repeatedly; check which version you cite. |
| DOI | [10.48550/arxiv.2312.10997](https://doi.org/10.48550/arxiv.2312.10997) |
| Citations (OpenAlex, 2026-09-13) | 733 |

**Abstract** *(verbatim, via OpenAlex)*

> Large Language Models (LLMs) showcase impressive capabilities but encounter challenges like hallucination, outdated knowledge, and non-transparent, untraceable reasoning processes. Retrieval-Augmented Generation (RAG) has emerged as a promising solution by incorporating knowledge from external databases. This enhances the accuracy and credibility of the generation, particularly for knowledge-intensive tasks, and allows for continuous knowledge updates and integration of domain-specific information. RAG synergistically merges LLMs' intrinsic knowledge with the vast, dynamic repositories of external databases. This comprehensive review paper offers a detailed examination of the progression of RAG paradigms, encompassing the Naive RAG, the Advanced RAG, and the Modular RAG. It meticulously scrutinizes the tripartite foundation of RAG frameworks, which includes the retrieval, the generation and the augmentation techniques. The paper highlights the state-of-the-art technologies embedded in each of these critical components, providing a profound understanding of the advancements in RAG systems. Furthermore, this paper introduces up-to-date evaluation framework and benchmark. At the end, this article delineates the challenges currently faced and points out prospective avenues for research and development.

**Why it matters for us.** The standard survey of RAG for LLMs. Use it to compress Related Work strand (c) into a few sentences with one citation rather than ten.

**What to take from it.** Nothing methodological — use it for taxonomy vocabulary (naive / advanced / modular RAG) so your architecture section can place itself in one sentence.

---

## Interpretable Long-Form Legal Question Answering with Retrieval-Augmented Large Language Models

**TIER 1 — legal domain analogue** · file: [`pdfs/07_LegalQA_LongForm_RAG_Louis2024.pdf`](pdfs/07_LegalQA_LongForm_RAG_Louis2024.pdf)

| | |
| --- | --- |
| Authors | Antoine Louis, Gijs van Dijck, Gerasimos Spanakis |
| Year | 2024 |
| Venue | AAAI 2024 (Proceedings of the AAAI Conference on Artificial Intelligence, 38(20)). |
| DOI | [10.1609/aaai.v38i20.30232](https://doi.org/10.1609/aaai.v38i20.30232) |
| Citations (OpenAlex, 2026-09-13) | 75 |

**Abstract** *(verbatim, via OpenAlex)*

> Many individuals are likely to face a legal dispute at some point in their lives, but their lack of understanding of how to navigate these complex issues often renders them vulnerable. The advancement of natural language processing opens new avenues for bridging this legal literacy gap through the development of automated legal aid systems. However, existing legal question answering (LQA) approaches often suffer from a narrow scope, being either confined to specific legal domains or limited to brief, uninformative responses. In this work, we propose an end-to-end methodology designed to generate long-form answers to any statutory law questions, utilizing a "retrieve-then-read" pipeline. To support this approach, we introduce and release the Long-form Legal Question Answering (LLeQA) dataset, comprising 1,868 expert-annotated legal questions in the French language, complete with detailed answers rooted in pertinent legal provisions. Our experimental results demonstrate promising performance on automatic evaluation metrics, but a qualitative analysis uncovers areas for refinement. As one of the only comprehensive, expert-annotated long-form LQA dataset, LLeQA has the potential to not only accelerate research towards resolving a significant real-world issue, but also act as a rigorous benchmark for evaluating NLP models in specialized domains. We publicly release our code, data, and models.

**Why it matters for us.** Long-form legal question answering with retrieval-augmented LLMs, with attention to interpretability and attribution. The closest analogue in the *legal* direction, as Telco-RAG is in the *telecom* direction. Your corpus sits at the intersection, which is the gap you should claim.

**What to take from it.** How they handle attribution and the evaluation of long-form legal answers — directly informs your H2 (groundedness) item and the 'quote the unsupported statement' follow-up.

---

## Benchmarking Large Language Models in Retrieval-Augmented Generation

**TIER 2 — RAG failure modes** · file: [`pdfs/08_Benchmarking_LLMs_in_RAG_Chen2024.pdf`](pdfs/08_Benchmarking_LLMs_in_RAG_Chen2024.pdf)

| | |
| --- | --- |
| Authors | Jiawei Chen, Hongyu Lin, Xianpei Han, Le Sun |
| Year | 2024 |
| Venue | AAAI 2024 (Proceedings of the AAAI Conference on Artificial Intelligence, 38(16)). |
| DOI | [10.1609/aaai.v38i16.29728](https://doi.org/10.1609/aaai.v38i16.29728) |
| Citations (OpenAlex, 2026-09-13) | 373 |

**Abstract** *(verbatim, via OpenAlex)*

> Retrieval-Augmented Generation (RAG) is a promising approach for mitigating the hallucination of large language models (LLMs). However, existing research lacks rigorous evaluation of the impact of retrieval-augmented generation on different large language models, which make it challenging to identify the potential bottlenecks in the capabilities of RAG for different LLMs. In this paper, we systematically investigate the impact of Retrieval-Augmented Generation on large language models. We analyze the performance of different large language models in 4 fundamental abilities required for RAG, including noise robustness, negative rejection, information integration, and counterfactual robustness. To this end, we establish Retrieval-Augmented Generation Benchmark (RGB), a new corpus for RAG evaluation in both English and Chinese. RGB divides the instances within the benchmark into 4 separate testbeds based on the aforementioned fundamental abilities required to resolve the case. Then we evaluate 6 representative LLMs on RGB to diagnose the challenges of current LLMs when applying RAG. Evaluation reveals that while LLMs exhibit a certain degree of noise robustness, they still struggle significantly in terms of negative rejection, information integration, and dealing with false information. The aforementioned assessment outcomes indicate that there is still a considerable journey ahead to effectively apply RAG to LLMs.

**Why it matters for us.** Benchmarks LLMs in RAG along noise robustness, negative rejection, information integration and counterfactual robustness. **'Negative rejection' is the published name for what your unanswerable stratum measures** (guideline.md §7.3.2, item H6).

**What to take from it.** Borrow the four ability dimensions to structure your failure taxonomy (RQ5), and cite 'negative rejection' when you justify the unanswerable stratum.

---

## Searching for Best Practices in Retrieval-Augmented Generation

**TIER 2 — ablation methodology** · file: [`pdfs/09_BestPractices_RAG_Wang2024.pdf`](pdfs/09_BestPractices_RAG_Wang2024.pdf)

| | |
| --- | --- |
| Authors | Xiaohua Wang, Zhenhua Wang, Xuan Gao, Feiran Zhang, Yixin Wu, Zhibo Xu et al. |
| Year | 2024 |
| Venue | EMNLP 2024, Main Conference (ACL Anthology 2024.emnlp-main.981). |
| DOI | [10.18653/v1/2024.emnlp-main.981](https://doi.org/10.18653/v1/2024.emnlp-main.981) |
| Citations (OpenAlex, 2026-09-13) | 103 |

**Abstract** *(verbatim, via OpenAlex)*

> Xiaohua Wang, Zhenghua Wang, Xuan Gao, Feiran Zhang, Yixin Wu, Zhibo Xu, Tianyuan Shi, Zhengyuan Wang, Shizheng Li, Qi Qian, Ruicheng Yin, Changze Lv, Xiaoqing Zheng, Xuanjing Huang. Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing. 2024.

**Why it matters for us.** A systematic search over RAG design choices. Useful as the citation for why a modular, one-axis-at-a-time ablation (which `scripts/run_experiments.py` implements) is the right way to study pipeline design.

**What to take from it.** The experimental-design table. Your Table 3 (conditions and held-constant parameters) should be at least as explicit.

---

## TelBench: A Benchmark for Evaluating Telco-Specific Large Language Models

**TIER 2 — telco-specific evaluation** · file: [`pdfs/10_TelBench_Lee2024.pdf`](pdfs/10_TelBench_Lee2024.pdf)

| | |
| --- | --- |
| Authors | Sunwoo Lee, Dhammiko Arya, Seung-Mo Cho, Gyoung-eun Han, Seokyoung Hong, Wonbeom Jang et al. |
| Year | 2024 |
| Venue | EMNLP 2024, Industry Track (ACL Anthology 2024.emnlp-industry.45). |
| DOI | [10.18653/v1/2024.emnlp-industry.45](https://doi.org/10.18653/v1/2024.emnlp-industry.45) |
| Citations (OpenAlex, 2026-09-13) | 4 |

**Abstract** *(verbatim, via OpenAlex)*

> Sunwoo Lee, Dhammiko Arya, Seung-Mo Cho, Gyoung-eun Han, Seokyoung Hong, Wonbeom Jang, Seojin Lee, Sohee Park, Sereimony Sek, Injee Song, Sungbin Yoon, Eric Davis. Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing: Industry Track. 2024.

**Why it matters for us.** A benchmark for telco-specific LLMs, from an industry track. Shows how operator-side telecom evaluation is being formalised.

**What to take from it.** Useful mainly to show breadth of the telecom-LLM evaluation literature in one or two Related Work sentences.

---

## TelecomGPT: A Framework to Build Telecom-Specfic Large Language Models

**TIER 3 — domain adaptation alternative** · file: [`pdfs/11_TelecomGPT_Zou2024.pdf`](pdfs/11_TelecomGPT_Zou2024.pdf)

| | |
| --- | --- |
| Authors | Hang Zou, Qiyang Zhao, Yu Tian, Lina Bariah, Faouzi Bader, Thierry Lestable et al. |
| Year | 2024 |
| Venue | arXiv:2407.09424. |
| DOI | [10.48550/arxiv.2407.09424](https://doi.org/10.48550/arxiv.2407.09424) |
| Citations (OpenAlex, 2026-09-13) | 7 |

**Abstract** *(verbatim, via OpenAlex)*

> Large Language Models (LLMs) have the potential to revolutionize the Sixth Generation (6G) communication networks. However, current mainstream LLMs generally lack the specialized knowledge in telecom domain. In this paper, for the first time, we propose a pipeline to adapt any general purpose LLMs to a telecom-specific LLMs. We collect and build telecom-specific pre-train dataset, instruction dataset, preference dataset to perform continual pre-training, instruct tuning and alignment tuning respectively. Besides, due to the lack of widely accepted evaluation benchmarks in telecom domain, we extend existing evaluation benchmarks and proposed three new benchmarks, namely, Telecom Math Modeling, Telecom Open QnA and Telecom Code Tasks. These new benchmarks provide a holistic evaluation of the capabilities of LLMs including math modeling, Open-Ended question answering, code generation, infilling, summarization and analysis in telecom domain. Our fine-tuned LLM TelecomGPT outperforms state of the art (SOTA) LLMs including GPT-4, Llama-3 and Mistral in Telecom Math Modeling benchmark significantly and achieve comparable performance in various evaluation benchmarks such as TeleQnA, 3GPP technical documents classification, telecom code summary and generation and infilling.

**Why it matters for us.** Builds telecom-specific LLMs by continued pre-training and fine-tuning. The main *alternative* to your approach: adapt the model rather than retrieve.

**What to take from it.** Cite as the design alternative you did not take, and say why — regulatory text changes, is jurisdiction-specific, and demands verbatim attribution to a numbered subsection, all of which favour retrieval over fine-tuning. This is a strong paragraph for your Introduction.

---

## Leveraging Fine-Tuned Retrieval-Augmented Generation with Long-Context Support: For 3GPP Standards

**TIER 3 — fine-tuned RAG over standards** · file: [`pdfs/12_TeleOracle_3GPP_RAG_Aly2024.pdf`](pdfs/12_TeleOracle_3GPP_RAG_Aly2024.pdf)

| | |
| --- | --- |
| Authors | Omar Erak, Nouf Alabbasi, Omar Alhussein, Ismail Lotfi, Hussein, Amr, Sami Muhaidat et al. |
| Year | 2024 |
| Venue | arXiv:2408.11775. |
| DOI | [10.48550/arxiv.2408.11775](https://doi.org/10.48550/arxiv.2408.11775) |
| Citations (OpenAlex, 2026-09-13) | 3 |

**Abstract** *(verbatim, via OpenAlex)*

> Recent studies show that large language models (LLMs) struggle with technical standards in telecommunications. We propose a fine-tuned retrieval-augmented generation (RAG) system based on the Phi-2 small language model (SLM) to serve as an oracle for communication networks. Our developed system leverages forward-looking semantic chunking to adaptively determine parsing breakpoints based on embedding similarity, enabling effective processing of diverse document formats. To handle the challenge of multiple similar contexts in technical standards, we employ a re-ranking algorithm to prioritize the most relevant retrieved chunks. Recognizing the limitations of Phi-2's small context window, we implement a recent technique, namely SelfExtend, to expand the context window during inference, which not only boosts the performance but also can accommodate a wider range of user queries and design requirements from customers to specialized technicians. For fine-tuning, we utilize the low-rank adaptation (LoRA) technique to enhance computational efficiency during training and enable effective fine-tuning on small datasets. Our comprehensive experiments demonstrate substantial improvements over existing question-answering approaches in the telecom domain, achieving performance that exceeds larger language models such as GPT-4 (which is about 880 times larger in size). This work presents a novel approach to leveraging SLMs for communication networks, offering a balance of efficiency and performance. This work can serve as a foundation towards agentic language models for networks.

**Why it matters for us.** Combines fine-tuning with long-context RAG over 3GPP standards. The hybrid of the two approaches above.

**What to take from it.** Cite alongside TelecomGPT when justifying the retrieval-only design decision.

---
