from clvm import eval_f

from ..patch_eval_f import patch_eval_f
from .bindings import BINDINGS


EVAL_F = patch_eval_f(eval_f, BINDINGS)
NEW_KEYWORDS = set(BINDINGS.keys())


"""
Copyright 2019 Chia Network Inc

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
