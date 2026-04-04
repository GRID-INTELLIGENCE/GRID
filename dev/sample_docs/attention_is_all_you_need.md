# Attention Is All You Need

## Abstract

The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. Transformer Architecture is a new simple network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

## Attention Mechanism

Attention Mechanism is a function that maps a query and a set of key-value pairs to an output. The output is computed as a weighted sum of the values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key.

## Multi-Head Attention

Multi-Head Attention is a technique that allows the model to jointly attend to information from different representation subspaces at different positions. Multi-Head Attention extends Attention Mechanism by running it in parallel across multiple learned projections.

## Positional Encoding

Positional Encoding is a method for injecting information about the relative or absolute position of tokens in the sequence. Since Transformer Architecture contains no recurrence and no convolution, Positional Encoding uses sinusoidal functions to represent position.

## Self-Attention

Self-Attention is a special case of Attention Mechanism where the queries, keys, and values all come from the same sequence. Self-Attention allows each position in a sequence to attend to all positions in the previous layer.

## Feed-Forward Network

Feed-Forward Network is a fully connected sub-layer applied to each position separately and identically. Each Feed-Forward Network uses two linear transformations with a ReLU activation in between.

## Encoder-Decoder Architecture

Encoder-Decoder Architecture is the overall structure of the Transformer model. The encoder maps an input sequence to a sequence of continuous representations, and the decoder generates an output sequence one element at a time. Encoder-Decoder Architecture uses Multi-Head Attention to connect encoder and decoder stacks.

Transformer Architecture builds on Encoder-Decoder Architecture and achieves state-of-the-art translation quality while being significantly more parallelizable.
