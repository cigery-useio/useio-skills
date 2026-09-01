# useio-skills

[UseIO](https://github.com/cigery-useio) 技能仓库——为 UseIO 桌面 AI 助手构建的可复用技能集合。每个技能是一份结构化的 SKILL.md 指令文档，Agent 按需加载后获得对应领域的专业工作流与规范约束。

## 技能列表

| 技能 | 说明 |
|------|------|
| [frontend-guidelines](./frontend-guidelines) | AI 开发 Web 前端的规范指引：版本基线、deprecated API 防幻觉清单、代码红线、界面设计质量（去 AI 味）、验证闭环工作流 |
| [vue-mastery](./vue-mastery) | Vue 3 专家技能：Composition API、script setup、响应式原理、组件架构、Pinia、测试与性能，适用于所有 Vue/Pinia/Router/Nuxt 工作 |
| [browser-automation](./browser-automation) | 浏览器自动化：控制 Chrome 执行多步骤网页操作——导航、点击输入、数据采集、表单填写、控制台与网络请求监控 |
| [debugger-pro](./debugger-pro) | 系统性调试：证据驱动的 6 阶段工作流，问题分级（P0-P3）、修复风险评估与门控、回归验证，输出完整调试报告 |
| [html-ppt-creator](./html-ppt-creator) | HTML 幻灯片制作：36 套主题、15 套 deck 模板、47 种动效、演讲者模式，打包为单 HTML 文件交付 |
| [prd-writer](./prd-writer) | 产品需求文档生成：结构化访谈 + 多模板选择，产出实施级 PRD，覆盖 B2B SaaS、数据平台、2C 移动端等场景及国内合规要求 |
| [knowledge-extractor](./knowledge-extractor) | 内置元技能 · 知识提取：从对话内容中提取有价值的知识条目，结构化保存到个人知识库 |
| [skill-generator](./skill-generator) | 内置元技能 · 技能生成：按标准化规范生成结构完整、逻辑闭环、脚本可执行的 SKILL.md，含能力边界约束与质量校验清单 |

## 技能结构

每个技能目录至少包含一个 `SKILL.md`，由两部分组成：

```
<skill-name>/
└── SKILL.md
    ├── YAML Front Matter   # name / description / triggerKeywords / version
    └── 正文章节             # 概述 → 输入规范 → 执行工作流 → 输出规范 → 异常处理
```

可选子目录：`scripts/`（辅助脚本）、`assets/`（模板与静态资源）。

## 使用方式

**内置元技能**（knowledge-extractor、skill-generator）随 UseIO 应用内置分发，无需安装与导入，随应用一起迭代升级，对话中直接触发即可。

**其他技能**：将技能目录放入应用数据目录的 `skills/` 下（或通过「技能管理」导入），重启后在对话中通过关键词触发或 `@技能` 引用。

## 创建新技能

创建新技能请遵循 [skill-generator](./skill-generator) 定义的标准化流程：kebab-case 命名、frontmatter 四字段规范、工作流闭环、UseIO 能力边界约束，并通过质量校验清单后提交。

## 提交规范

- 技能目录名与 frontmatter `name` 字段保持一致
- 提交信息使用英文，格式：`feat: add <skill-name> skill for <purpose>`
