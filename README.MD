# Explicit Semantic Text Representation Library
This library is being designed with the goal to learn explicit operations over unstructured text.
## Disclaimer
The repository is under heavy development. Here be dragons.
## installation
```bash
git clone http://github.com/semanchester/estrella
```
The library does not come as a stand-alone and does not provide a pip-compatible installer but you can use it as a git submodule, for instance: 
```bash
git submodule add http://github.com/semanchester/estrella
```
## Usage
Example:
```python
from estrella.util import read_config
from estrella.main import Estrella
cfg = read_config(path="path/to/hocon_file") # merges with default config
main = Estrella(cfg)
main.run_pipeline("default_pipeline", location="your/path/to/files")
from estrella.model.oie import ContextLabel
# Why did the chicken cross the road?
result = main.docs.hop(link_name="facts").filter(subject="chicken", predicate="cross", object="the road").hop(link_name="links",constraint=lambda link: 
link.label == ContextLabel.Background)
from estrella.serialize.readable.oie import simple_print
result.serialize(serialize_with=simple_print)

```
For documentation, refer to the source code.

In general, `Pipeline`s are used to read text and enrich it with external information (such as word embeddings or information extraction). The `default_pipeline` for example, defined in the default config `config/default.conf` will read a plain text file and convert it our internal representation. `extended_pipeline` will do just that and in addition enrich the words with word2vec embeddings and extract information from the text.
`View`s implement operations over collections of `Concept`s, such as `Fact`s and can be serialized to be interpreted by humans or further processed with other tools.