# Models

Serialized classifier models with corresponding training and testing scripts.
## Directories

* `embedder` - [`FastText`](https://fasttext.cc/) word embedder model for token text vectorization (self-trained, with source)
* `names` - training and test scripts for function name classifiers

## Files
Naming convention for model files is `<classifier set>_<classifier name>.<serialization source>`.

* `*.joblib` - classifier models serialized with [`joblib`](https://pypi.org/project/joblib/)
* `*.ft` - FastText model serialized with [`gensim.models.FastText`](https://radimrehurek.com/gensim/models/fasttext.html)
