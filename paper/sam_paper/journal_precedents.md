# Journal precedents — articles from *Telematics and Informatics* itself

**What this file is.** Fifteen articles published in the target journal (ISSN 0736-5853), selected as the closest precedents to this project. For each one: verified bibliographic metadata, the abstract where it is openly available, why it matters for our submission, and what specifically to imitate.

**Why there are no PDFs here.** These articles are published by Elsevier on ScienceDirect, which returns HTTP 403 to automated requests. Several are hybrid open access under CC-BY and can be downloaded freely **from a browser**; the rest are subscription-only and should be obtained through your institutional access. The DOI link is given for each. Nothing here was scraped or redistributed.

**How the metadata was obtained.** Crossref API (journal record and works list for ISSN 0736-5853), OpenAlex (authorship, biblio, open-access status, abstracts), Semantic Scholar (abstracts where OpenAlex had none). Retrieved 2026-09-13. Where no open source carried an abstract, this file says so rather than paraphrasing from memory.

**Tiers.** TIER 1 = read in full before drafting. TIER 2 = read the introduction and method. TIER 3 = cite, skim.

---

## Beyond accuracy: assessing the information quality of large language models for systematic literature reviews

**TIER 1 — closest structural template**

| | |
| --- | --- |
| Authors | Huiqian Lai, Yiqi Li |
| Published | 2026-07-28 |
| Volume / pages | 109 / 102447 |
| DOI | [10.1016/j.tele.2026.102447](https://doi.org/10.1016/j.tele.2026.102447) |
| Access | open access — hybrid, CC-BY |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** *(verbatim, via OpenAlex)*

> Systematic literature reviews (SLRs) are increasingly supported by large language models (LLMs), but existing evaluations rarely go beyond accuracy and overlook broader information quality dimensions. This study provides an Information Quality (IQ)-driven evaluation of LLM support for SLR tasks in communication research, focused on diagnosing failure modes and their implications for responsible use. Using 1,325 articles on cross-platform social media research, we design a seven-step evaluation pipeline that mirrors core SLR decisions and maps them onto contextual, intrinsic, and representational IQ dimensions. Two leading LLMs, GPT-4o and Claude 3.7 Sonnet, classify or extract information about article type and empirical status (empirical vs. non-empirical), data sources (e.g., media types and platform names), data collection methods, and the number and names of social media platforms. Validated human-coded annotations serve as ground truth, and mixed-method insights are reported from both quantitative performance analysis and qualitative error analysis. Both models achieve near-perfect accuracy for document type identification, yet their performance on tasks requiring boundary-setting judgments, methodological interpretation, or exact structured extraction is lower and more variable. Qualitative error analysis reveals that both models rely on surface-level cues rather than holistic reasoning; they apply narrow rules mechanically and fail to reconcile conflicting signals across different parts of a paper. The two models also exhibit task-specific error profiles rather than stable opposite decision biases: for example, GPT-4o is more conservative in digital trace detection but more expansive in platform-count extraction, while Claude 3.7 Sonnet shows stronger performance on grounded platform extraction. We conclude that current LLMs can reliably assist, but not replace, human judgment in SLRs. Effective deployment requires making model reasoning visible, designing prompts that account for the full range of methods in a field, and using models with complementary task-specific error profiles to flag ambiguous cases for human review.

**Why it matters for us.** This is the paper to model. It is an *evaluation* paper about LLM output quality, published by your target journal in 2026. It uses human-coded annotations as ground truth, evaluates two LLMs on a multi-step pipeline, reports quantitative performance **and** a qualitative error analysis, and concludes with an 'assist, not replace' boundary. That is exactly the shape of the paper described in guideline.md §3 Framing A.

**What to imitate.** The seven-step evaluation pipeline framing; mapping task steps onto named quality dimensions; pairing quantitative agreement with qualitative failure-mode analysis; the concluding move from findings to responsible-use guidance. Also note how little space the tooling gets.

---

## A search changer: auditing Google’s AI overviews interface in political and news search

**TIER 1 — audit-study template**

| | |
| --- | --- |
| Authors | Shir Weinbrand |
| Published | 2026-05-14 |
| Volume / pages | 107 / 102417 |
| DOI | [10.1016/j.tele.2026.102417](https://doi.org/10.1016/j.tele.2026.102417) |
| Access | open access — hybrid, CC-BY |
| Citations (OpenAlex, 2026-09-13) | 1 |

**Abstract** *(verbatim, via OpenAlex)*

> Google’s AI Overviews (AIOs) − AI-generated summaries − mark a shift from information retrieval to AI-driven curation, raising underexplored questions about political and news exposure and algorithmic gatekeeping. This study presents the first systematic mapping of AIOs in these domains, examining their presence on desktop ( RQ1a ) and mobile ( RQ1b ) and their relationship to query characteristics ( RQ2a , RQ2b ). Using interface and algorithm auditing, I develop taxonomies of AIO elements, apply hierarchical cluster analysis to identify structural types, and run regression models to predict these from query characteristics. Findings show AIOs are neither uniform nor neutral: political issue queries tend to trigger comprehensive AIOs, while news politics queries elicit more restrained responses. The proposed taxonomies offer a transferable framework for cross-platform comparisons of AI-powered search and a foundation for future auditing and accountability research amid a major transformation in the search landscape

**Why it matters for us.** A systematic audit of a deployed AI information interface (Google's AI Overviews) in a domain where errors have civic consequences. Shows that this journal will publish rigorous, methods-heavy empirical work on generative AI systems provided the framing is about information exposure and gatekeeping rather than about the model.

**What to imitate.** Explicit RQ labelling (RQ1a, RQ1b, RQ2a, RQ2b) carried through Results; building a taxonomy from observed data then modelling it; the 'neither uniform nor neutral' style of conclusion that lands a governance point without moralising.

---

## Automating the identification of High-Value Datasets in open government data portals: A US municipalities case study

**TIER 1 — build-and-assess template**

| | |
| --- | --- |
| Authors | Alfonso Quarati, Anastasija Nikiforova |
| Published | 2026-05-06 |
| Volume / pages | 107 / 102415 |
| DOI | [10.1016/j.tele.2026.102415](https://doi.org/10.1016/j.tele.2026.102415) |
| Access | open access — hybrid, CC-BY |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** *(verbatim, via OpenAlex)*

> Recognized for fostering innovation and transparency, driving economic growth, enhancing public services, supporting research, empowering citizens, and promoting environmental sustainability, High-Value Datasets (HVD) play a crucial role in the broader Open Government Data (OGD) movement. However, identifying HVD presents a resource-intensive and complex challenge due to the nuanced nature of data value. Our proposal aims to automate the identification of HVDs on OGD portals using a quantitative approach based on a detailed analysis of user interest derived from data usage statistics, thereby minimizing the need for human intervention. The proposed method involves programmatically extracting download data via APIs, analyzing metrics to identify high-value categories, and comparing HVD datasets across different portals. This automated process provides valuable insights into trends in dataset usage, reflecting citizens’ needs and preferences. The effectiveness of our approach is demonstrated through its application to a sample of 9 US OGD city portals, involving the analysis of approximately 17,000 datasets. Findings show that the method successfully isolates a small core of high-impact datasets from the broader population, providing a scalable tool for data prioritization. The practical implications of this study include contributing to the understanding of HVD at both local and national levels. By providing a systematic and efficient means of identifying HVD, our approach aims to inform open governance initiatives and practices, aiding OGD portal managers and public authorities in their efforts to optimize data dissemination and utilization.

**Why it matters for us.** A genuine artefact paper in this journal: the authors build an automated method and evaluate it, but frame the whole thing inside open government data and public value. This is the proof that a system CAN be published here — and a demonstration of exactly how much socio-technical framing it takes.

**What to imitate.** How the Introduction spends its words on why the problem matters to the public sector before any method appears; 'minimising the need for human intervention' as the stated value proposition; the case-study structure (one jurisdiction, defended as a case rather than apologised for).

---

## Human–chatbot interaction, social support and public value co-creation: Evidence from users of government chatbots in China

**TIER 1 — government chatbot in this journal**

| | |
| --- | --- |
| Authors | Houcai Wang, Thompson S.H. Teo |
| Published | 2026-02-01 |
| Volume / pages | 105 / 102380 |
| DOI | [10.1016/j.tele.2026.102380](https://doi.org/10.1016/j.tele.2026.102380) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 1 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** The most directly comparable application area: users of *government* chatbots, studied for public value co-creation. Cite it in Related Work strand (a). It anchors your claim that AI-mediated access to government information is an established concern of this venue.

**What to imitate.** The public-value vocabulary. Borrow the framing language even though your method is different.

---

## When AI lies to me: understanding user recognition, attribution, and response to AI hallucinations in human-AI interaction

**TIER 2 — hallucination, user-side**

| | |
| --- | --- |
| Authors | Shu Fan, Xueqi Wang, Bingqian Zhang, Xiaobei Sun |
| Published | 2026-06-24 |
| Volume / pages | 108 / 102434 |
| DOI | [10.1016/j.tele.2026.102434](https://doi.org/10.1016/j.tele.2026.102434) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** Studies how users recognise, attribute and respond to AI hallucinations. Directly relevant to your H2 (groundedness) and H5 (decision usability) items, and to the Discussion: what happens when a fluent wrong answer reaches a non-expert.

**What to imitate.** Use it to justify why groundedness must be measured by humans and not only by an LLM judge, and to frame the expertise-moderation hypothesis (RQ4).

---

## Unequal AI readiness: institutional and digital disparities in e-government across the European Union

**TIER 2 — e-government AI readiness**

| | |
| --- | --- |
| Authors | Eduardo Amaral, Mijail Naranjo-Zolotov, Fernando Bação |
| Published | 2026-04-16 |
| Volume / pages | 107 / 102400 |
| DOI | [10.1016/j.tele.2026.102400](https://doi.org/10.1016/j.tele.2026.102400) |
| Access | open access — hybrid, CC-BY |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** *(verbatim, via OpenAlex)*

> Artificial Intelligence (AI) is increasingly being integrated into public governance, enabling more adaptive, predictive, and autonomous public services. Despite its potential, the extent to which European Union member states are ready to adopt AI in electronic government remains underexplored. To address this gap, AI readiness across European Union countries is assessed and clustered based on institutional and technological conditions. Using secondary data from Eurostat and the European Commission’s electronic Government Benchmark, exploratory factor analysis reveals two latent dimensions: Digital Skills and Electronic Government Engagement, and Transparency and Electronic Government Service Availability. These dimensions are used as inputs for hierarchical and k-means clustering, resulting in six distinct country groups reflecting varying profiles of AI readiness. Our findings suggest that effective AI integration is associated with both institutional capacity and citizen preparedness, linking digital divide patterns to AI readiness levels. This study provides a comparative, data-driven assessment of AI readiness across the European Union, identifying latent dimensions that can inform targeted policy interventions and support inclusive digital transformation.

**Why it matters for us.** Assesses readiness to adopt AI in electronic government across the EU. Useful as the counterpoint that motivates your setting: readiness research is concentrated on high-income jurisdictions.

**What to imitate.** Cite in the Introduction to establish the gap your Bangladesh case fills. Note the secondary-data method — a reminder that this journal accepts a wide range of designs.

---

## Digital public management reform: assessing the impact of e-government initiatives on administrative transparency

**TIER 2 — e-government and transparency**

| | |
| --- | --- |
| Authors | Jinlin Ma |
| Published | 2026-05-12 |
| Volume / pages | 107 / 102418 |
| DOI | [10.1016/j.tele.2026.102418](https://doi.org/10.1016/j.tele.2026.102418) |
| Access | open access — hybrid, CC-BY |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** *(verbatim, via OpenAlex)*

> • Digital Transformation in Governance: Examines the role of e-government initiatives in enhancing transparency and citizen trust in public administration. • Quantitative Analysis: Uses structured surveys from 320 citizens to assess perceptions of digital services and their impact on transparency. • Key Drivers Identified: Finds that information accessibility (β = 0.454) and digital adoption (β = 0.443) are the most significant factors driving transparency. • Strong Impact on Trust: Demonstrates that e-government initiatives positively influence citizen trust, with a correlation of r = 0.824 and adjusted R 2 = 0.76. • Actionable Insights for Governments: Offers evidence-based guidance for designing more accountable, citizen-centric digital public management systems. • Policy Relevance: Provides valuable insights for policymakers seeking to reduce corruption and enhance service delivery through digital tools. Digital transformation has become a defining pillar of modern public administration, with governments increasingly adopting e-government initiatives to enhance service delivery and citizen engagement. However, the improvement in administrative transparency these initiatives achieve remains insufficiently understood. This study addresses this gap by developing an integrated framework to assess how e-government initiatives enhance administrative transparency, quantitatively linking digital adoption, service efficiency and information accessibility to reductions in corruption and improvements in citizen trust, thereby providing evidence-based guidance for designing accountable public management systems. Data were collected from 320 citizens using structured surveys and analyzed descriptively to summarize key perceptions of digital service usage. Pearson correlation analysis was then employed to examine the strength and direction of relationships between e-government adoption. Similarly, regression modelling was applied to assess the overall predictive influence of digital public management reform factors on transparency and citizen trust in government processes. Findings show e government initiatives strongly boost transparency and trust, with r = 0.824 and adjusted R 2 = 0.76. These results highlight that information accessibility ( β = 0.454) and digital adoption ( β = 0.443) are the most influential drivers of transparency, offering actionable insights for governments seeking to design more accountable and citizen-centric digital ecosystems.

**Why it matters for us.** Survey-based study linking e-government initiatives to administrative transparency and citizen trust. Represents the dominant empirical style in this journal.

**What to imitate.** Read it mainly to calibrate register and the expected density of theory. Also note the Highlights style: each bullet states a result with a number.

---

## Open government data portal usability: A user-centred usability analysis of 41 open government data portals

**TIER 2 — user-centred evaluation precedent**

| | |
| --- | --- |
| Authors | Anastasija Nikiforova, Keegan McBride |
| Published | 2020-11-30 |
| Volume / pages | 58 / 101539 |
| DOI | [10.1016/j.tele.2020.101539](https://doi.org/10.1016/j.tele.2020.101539) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 140 |

**Abstract** *(verbatim, via SemanticScholar)*

> Open government data, as a phenomena, may be considered an important and influential innovation that has the potential to drive the creation of public value via enabling the prevention of corruption, increase in accountability and transparency, and driving the co-creation of new and innovative services. However, in order for open government data to be fully taken advantage of, it must be found, understood, and used. Though many countries maintain open government data portals, the usability of said portals can vary greatly; this is important to understand as the usability of a portal likely impacts the eventual reuse of the data made available there. Acknowledging the importance of portal usability to the data reuse process, this paper helps to elucidate some initial insights by asking two questions: “How can the usability of open government data portals be evaluated and compared across contexts?” and “What are the most commonly missing usability aspects from open government data portals?”. In order to answer these research questions, a subset of 41 national open government data portals were selected for an in-depth usability analysis drawing on the feedback from 40 individual users. As a result of this analysis, the paper is able to make three primary contributions: (1) the validation of a framework for open government data portal usability analysis, (2) develops an initial comparative international ranking of open government data portal usability, and (3) identifies commonly occurring portal usability strengths and weaknesses across contexts.

**Why it matters for us.** A user-centred usability analysis of 41 open government data portals; 140 citations. The best in-journal precedent for a *systematic human evaluation of a public information system*.

**What to imitate.** The instrument design and how it is reported; the argument that findability and usability determine whether public information is actually reusable — which is precisely your Introduction's argument about regulatory text.

---

## E-Government service delivery by a local government agency: The case of E-Licensing

**TIER 3 — licensing e-government**

| | |
| --- | --- |
| Authors | Pathamanathan Pitchay Muthu Chelliah, Ramayah Thurasamy, Ahmed Ibrahim Alzahrani, Osama Alfarraj, Nasser Alalwan |
| Published | 2016-02-19 |
| Volume / pages | 33 / 925–935 |
| DOI | [10.1016/j.tele.2016.02.003](https://doi.org/10.1016/j.tele.2016.02.003) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 44 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** E-government service delivery for **e-licensing** by a local government agency. The subject matter overlaps your corpus (licensing procedure) even though the method is an adoption study.

**What to imitate.** Cite for the licensing-as-public-service framing; useful for one or two sentences in the Introduction about the administrative burden of licensing regimes.

---

## Sustainability of telecentres in developing countries: Lessons from Union Digital Centre in Bangladesh

**TIER 3 — Bangladesh precedent**

| | |
| --- | --- |
| Authors | Md. Gofran Faroqi, Noore Alam Siddiquee, Shahid Ullah |
| Published | 2018-05-09 |
| Volume / pages | 37 / 113–127 |
| DOI | [10.1016/j.tele.2018.05.006](https://doi.org/10.1016/j.tele.2018.05.006) |
| Access | open access — green, CC-BY-NC-ND |
| Citations (OpenAlex, 2026-09-13) | 19 |

**Abstract** *(verbatim, via SemanticScholar)*

> This study examines operational sustainability of a major telecentre initiative - the Union Digital Centre (UDC) in Bangladesh - from the perspective of public-private-people’s partnership (PPPP). Given the rising incidence of dropout of private entrepreneurs causing premature closure of telecentres, it is important to understand and identify key variables that affect sustainability of the scheme. In appreciation of the difficulty associated with operationalisation of the term ‘sustainability’ in this study we adopt ‘operational sustainability’ as an alternative to investigate the dynamics of sustenance. We have reviewed key literature about various dimensions of sustainability and their interrelationships in order to develop hypotheses about sustainability of the UDC and factors associated with it. Drawing on data collected from a survey of 538 private entrepreneurs and 41 interviews with government officials we show the extent to which various elements of the UDC eco-system contribute to its sustainability. The application of a structural equation model confirms that both financial and social outcomes of the UDC depend largely on inputs and contributions of various stakeholders. The paper concludes that effective engagement of private entrepreneurs is critical, as is governmental patronage, for ensuring operational sustainability of partnership-based telecentres like the UDC.

**Why it matters for us.** One of only two Bangladesh-focused articles in the journal's entire 2,844-record back catalogue. Green OA (author accepted manuscript available via Flinders Academic Commons).

**What to imitate.** Cite it to establish that the journal has published Bangladeshi ICT research, and to borrow its framing of digital service delivery constraints in the country. Its 'operational sustainability' construct is a useful model for defining a term carefully before measuring it.

---

## Exploring generative AI in the misinformation Era: Impacts as a misinformation source and fact-checker on belief in the information

**TIER 3 — generative AI and information belief**

| | |
| --- | --- |
| Authors | Seo Yoon Lee, Weizi Liu |
| Published | 2025-07-26 |
| Volume / pages | 101 / 102308 |
| DOI | [10.1016/j.tele.2025.102308](https://doi.org/10.1016/j.tele.2025.102308) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 6 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** Generative AI as both a misinformation source and a fact-checker, and the effect on belief. Relevant to the risk half of your Discussion.

**What to imitate.** Use for the argument that fluent generated text changes what people believe — the mechanism behind the risk your H5 item measures.

---

## Digital competence of AI chatbot users: scale development and its relationships with smart customer experience, trust, and reuse intention

**TIER 3 — chatbot competence scale**

| | |
| --- | --- |
| Authors | Heeseung Yu, Ye Sang, Eunkyoung Han |
| Published | 2026-03-18 |
| Volume / pages | 106 / 102392 |
| DOI | [10.1016/j.tele.2026.102392](https://doi.org/10.1016/j.tele.2026.102392) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 2 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** Scale development for digital competence of AI chatbot users, related to trust and reuse intention.

**What to imitate.** Relevant only if you later pursue Framing C (adoption study). Skim.

---

## When chatbots make errors: Cognitive and affective pathways to understanding forgiveness of chatbot errors

**TIER 3 — chatbot error tolerance**

| | |
| --- | --- |
| Authors | Bolin Cao, Zhenming Li, Li Jiang |
| Published | 2024-09-23 |
| Volume / pages | 94 / 102189 |
| DOI | [10.1016/j.tele.2024.102189](https://doi.org/10.1016/j.tele.2024.102189) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 31 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** Cognitive and affective pathways to forgiving chatbot errors; 31 citations.

**What to imitate.** Useful for one Discussion sentence about error tolerance being lower in high-stakes regulatory contexts than in the consumer settings most of this literature studies.

---

## User perception and self-disclosure towards an AI psychotherapy chatbot according to the anthropomorphism of its profile picture

**TIER 3 — chatbot perception**

| | |
| --- | --- |
| Authors | Jieon Lee, Daeho Lee |
| Published | 2023-09-27 |
| Volume / pages | 85 / 102052 |
| DOI | [10.1016/j.tele.2023.102052](https://doi.org/10.1016/j.tele.2023.102052) |
| Access | closed (institutional access needed) |
| Citations (OpenAlex, 2026-09-13) | 74 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** User perception and self-disclosure toward an AI psychotherapy chatbot; 74 citations. Representative of the journal's high-citation chatbot work.

**What to imitate.** Background only. Shows what 'a chatbot paper' normally means in this venue — and therefore how differently you must position yours.

---

## Understanding AI’s role in society and workplace through technology, trust, and anticipatory emotion factors

**TIER 3 — AI trust framing**

| | |
| --- | --- |
| Authors | Chaeyeon Yim, Carolyn A. Lin |
| Published | 2026-04-25 |
| Volume / pages | 107 / 102405 |
| DOI | [10.1016/j.tele.2026.102405](https://doi.org/10.1016/j.tele.2026.102405) |
| Access | open access — green |
| Citations (OpenAlex, 2026-09-13) | 0 |

**Abstract** — not available through any open metadata source (Crossref, OpenAlex, Semantic Scholar). Read it on the publisher page.

**Why it matters for us.** AI's role in society and the workplace via technology, trust and anticipatory emotion factors.

**What to imitate.** Background for the trust vocabulary in your Discussion.

---
