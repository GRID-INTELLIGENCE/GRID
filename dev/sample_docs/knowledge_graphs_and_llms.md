# Knowledge Graphs and Large Language Models: A Survey

## Abstract

Large Language Models (LLMs) have demonstrated remarkable capabilities but suffer from hallucination and stale parametric knowledge. Knowledge Graph is a structured representation of facts as a set of entities and typed relationships. Combining Knowledge Graphs with LLMs addresses complementary weaknesses in both approaches.

## Knowledge Graph

Knowledge Graph is a structured knowledge base that stores factual information as a graph of entities connected by typed relationships. Knowledge Graph uses triples of the form (subject, predicate, object) to represent facts. Knowledge Graph contrasts with unstructured text by providing explicit, queryable structure.

## Entity Linking

Entity Linking is the process of mapping mentions in text to their corresponding entities in a Knowledge Graph. Entity Linking builds on Named Entity Recognition to resolve surface forms to canonical identifiers. Entity Linking uses Knowledge Graph to disambiguate ambiguous mentions.

## Graph Neural Network

Graph Neural Network is a class of neural network architectures that operate on graph-structured data. Graph Neural Network extends standard neural networks to handle non-Euclidean data. Graph Neural Network uses message-passing between neighboring nodes to aggregate structural information.

## Knowledge Graph Embedding

Knowledge Graph Embedding is a representation learning method that maps entities and relationships to dense vectors. Knowledge Graph Embedding uses TransE, RotatE, or similar models to learn geometric relationships between entities. Knowledge Graph Embedding builds on Knowledge Graph to enable similarity-based reasoning.

## Hallucination Mitigation

Hallucination Mitigation is the goal of reducing the tendency of language models to generate factually incorrect statements. Knowledge Graph provides structured grounding that improves Hallucination Mitigation. Retrieval-Augmented Generation is another approach to Hallucination Mitigation that fetches evidence at inference time.

## Subgraph Retrieval

Subgraph Retrieval is the process of extracting a relevant portion of a Knowledge Graph to answer a query. Subgraph Retrieval uses Entity Linking to identify anchor nodes and Graph Neural Network to expand the neighborhood. Subgraph Retrieval builds on Knowledge Graph Embedding for ranking candidate triples.
