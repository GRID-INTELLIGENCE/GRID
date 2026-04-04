# Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

## Abstract

Large pre-trained language models have been shown to store factual knowledge in their parameters. Retrieval-Augmented Generation (RAG) is a technique that combines parametric memory with non-parametric memory for language generation. RAG contrasts with pure parametric models by grounding generation in retrieved evidence.

## Retrieval-Augmented Generation

Retrieval-Augmented Generation is a hybrid approach that augments language model generation with retrieved documents. RAG uses a retriever to find relevant passages and a generator to produce output conditioned on both the input and retrieved context.

## Dense Passage Retriever

Dense Passage Retriever is a bi-encoder model that encodes queries and passages into dense vector representations. Dense Passage Retriever uses Retrieval-Augmented Generation as the retrieval backbone. Dense Passage Retriever extends traditional BM25 sparse retrieval with learned dense embeddings.

## Sequence-to-Sequence Generator

Sequence-to-Sequence Generator is a language model conditioned on both a query and retrieved passages. The generator in RAG is a Sequence-to-Sequence Generator that produces the final answer. Sequence-to-Sequence Generator uses BART or T5 as the underlying model architecture.

## Vector Index

Vector Index is a data structure for approximate nearest-neighbor search over dense embeddings. Dense Passage Retriever relies on a Vector Index (typically FAISS) to retrieve relevant passages at inference time. Vector Index builds on embedding similarity to enable sub-linear retrieval time.

## Knowledge Grounding

Knowledge Grounding is the property of a model output being supported by retrieved evidence rather than hallucinated parametric memory. Retrieval-Augmented Generation improves Knowledge Grounding by conditioning generation on real retrieved documents. Knowledge Grounding contrasts with hallucination in generative models.

## Open-Domain Question Answering

Open-Domain Question Answering is the task of answering factual questions without restricting the domain of possible answers. Retrieval-Augmented Generation significantly improves Open-Domain Question Answering by providing a retrieval step before generation.
