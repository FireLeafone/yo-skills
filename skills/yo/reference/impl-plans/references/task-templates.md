# 任务模板

根据 `impl-plans` 中选择的验证策略，使用对应模板撰写任务。

---

## TDD 任务模板

适用于：`tdd-per-task`

当任务定义明确、边界清晰、适合单元测试时使用。

````markdown
### 任务 N: [组件名称]

**文件：**
- 创建: `exact/path/to/file.py`
- 修改: `exact/path/to/existing.py:123-145`
- 测试: `tests/exact/path/to/test.py`

**验证策略：** `tdd-per-task`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `pytest tests/path/test.py::test_name -v`
预期: 失败，提示 "function not defined"

- [ ] **步骤 3: 编写最简实现**

```python
def function(input):
    return expected
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `pytest tests/path/test.py::test_name -v`
预期: 通过

- [ ] **步骤 5: 提交** (若需要)

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

---

## 实现-only 任务模板

适用于：`batched-verification` 中的实现阶段

测试将集中到同组的“验证任务”中统一编写和运行。本任务只关注正确实现。

````markdown
### 任务 N: [组件名称]

**文件：**
- 创建: `exact/path/to/file.py`
- 修改: `exact/path/to/existing.py:123-145`

**验证策略：** `batched-verification`（实现-only）

- [ ] **步骤 1: 编写实现**

```python
def function(input):
    return expected
```

- [ ] **步骤 2: 本地验证**

运行: `python -m py_compile src/path/file.py`
预期: 无语法错误

- [ ] **步骤 3: 提交** (若需要)

```bash
git add src/path/file.py
git commit -m "feat: add specific feature"
```
````

---

## 批量验证任务模板

适用于：`batched-verification` 中的验证阶段

为一组前置实现任务补充测试并运行。必须列出覆盖的任务编号。

````markdown
### 任务 N: 验证 [功能组名称]

**文件：**
- 创建: `tests/exact/path/to/test.py`

**验证策略：** `batched-verification`（验证任务）

**覆盖的实现任务：** 任务 2、任务 3、任务 4

- [ ] **步骤 1: 为覆盖的任务编写测试**

```python
def test_task_2_specific_behavior():
    result = function(input)
    assert result == expected

def test_task_3_edge_case():
    ...
```

- [ ] **步骤 2: 运行测试**

运行: `pytest tests/path/test.py -v`
预期: 全部通过

- [ ] **步骤 3: 提交** (若需要)

```bash
git add tests/path/test.py
git commit -m "test: add tests for feature group"
```
````

---

## 无新测试任务模板

适用于：`existing-coverage`

不新增测试，但仍需说明如何验证。

````markdown
### 任务 N: [任务名称]

**文件：**
- 修改: `exact/path/to/config.yaml`
- 修改: `docs/feature.md`

**验证策略：** `existing-coverage`

- [ ] **步骤 1: 应用变更**

```yaml
# config.yaml
setting: new-value
```

- [ ] **步骤 2: 验证变更**

运行: `pytest tests/path/test_existing.py -v`
预期: 通过，无回归

或手动验证：
- 打开 `docs/feature.md` 确认描述准确
- 运行 `make lint` 无错误

- [ ] **步骤 3: 提交** (若需要)

```bash
git add config.yaml docs/feature.md
git commit -m "chore: update config and docs"
```
````

---

## 使用提示

- 选择模板前先确认该任务的验证策略。
- 若同一计划混合多种策略，在任务开头明确标注。
- “提交”步骤是否保留，取决于用户是否要求每个任务都提交。
