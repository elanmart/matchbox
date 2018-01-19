import torch

class AbstractBatch(object):
    pass

class VectorBatch(AbstractBatch):
    pass

class MaskedBatch(AbstractBatch):

    def __init__(self, data, mask, dims):
        if data.dim() != mask.dim() or mask.dim() != len(dims) + 1:
            raise ValueError("malformed batch object")
        self.data = data
        self.mask = mask
        self.dims = dims

    @classmethod
    def fromlist(cls, examples, dims):
        # do some validation
        bs = len(examples)
        sizes = [max(x.size(d + 1) for x in examples) for d in range(len(dims))]
        data = examples[0].new(bs, *sizes).zero_()
        mask_sizes = [s if dims[d] else 1 for d, s in enumerate(sizes)]
        mask = examples[0].new(bs, *mask_sizes).zero_()
        for i, x in enumerate(examples):
            inds = [slice(0, x.size(d + 1)) if b else slice(None)
                    for d, b in enumerate(dims)]
            data.__setitem__((slice(i, i + 1), *inds), x)
            mask.__setitem__((slice(i, i + 1), *inds), 1)
        return cls(data, mask, dims)

    def __repr__(self):
        return "MaskedBatch {} with:\n data: {}\n mask: {}".format(
            repr(self.dims), repr(self.data), repr(self.mask))

    def cuda(self):
        data = self.data.cuda()
        mask = self.mask.cuda()
        return self.__class__(data, mask, self.dims)

    def transpose(self, dim1, dim2):
        data = self.data.transpose(dim1, dim2)
        mask = self.mask.transpose(dim1, dim2)
        dims = list(self.dims)
        dims[dim1 - 1], dims[dim2 - 1] = dims[dim2 - 1], dims[dim1 - 1]
        dims = tuple(dims)
        return self.__class__(data, mask, dims)

if torch.__version__ < '0.4':
    def var_new(self, *args, **kwargs):
        n = self.data.new(*args, **kwargs)
        return torch.autograd.Variable(n)
    torch.autograd.Variable.new = var_new

    def embed_forward(self, input):
        return torch.nn.functional.embedding(
            input, self.weight, self.padding_idx, self.max_norm,
            self.norm_type, self.scale_grad_by_freq, self.sparse)
    torch.nn.Embedding.forward = embed_forward