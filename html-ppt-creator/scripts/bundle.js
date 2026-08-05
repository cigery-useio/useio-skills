#!/usr/bin/env node
/**
 * html-ppt-creator :: bundle.js
 *
 * 单文件打包脚本 - 将 HTML 中所有外部引用的 CSS/JS 内联到单个 HTML 文件中。
 * 产出的单文件可拷贝发送给他人，双击即可在浏览器中播放，无需任何外部依赖。
 *
 * 用法：
 *   node bundle.js --input <deck.html> --output <presentation.html> --skill-dir <dir>
 *
 * 依赖：Node.js 白名单模块（fs, path, os）- 零第三方依赖
 *
 * 工作原理：
 *   1. 读取输入 HTML
 *   2. 正则匹配所有 <link rel="stylesheet" href="..."> 标签
 *   3. 读取对应 CSS 文件内容，替换为内联 <style> 块
 *   4. 正则匹配所有 <script src="..."> 标签
 *   5. 读取对应 JS 文件内容，替换为内联 <script> 块
 *   6. 写入输出 HTML 文件
 */

'use strict'

const fs = require('fs')
const path = require('path')
const os = require('os')

/**
 * 解析命令行参数
 * @returns {{input: string, output: string, skillDir: string}}
 */
const parseArgs = () => {
  const args = process.argv.slice(2)
  const params = {}
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--input' && args[i + 1]) {
      params.input = args[++i]
    } else if (args[i] === '--output' && args[i + 1]) {
      params.output = args[++i]
    } else if (args[i] === '--skill-dir' && args[i + 1]) {
      params.skillDir = args[++i]
    }
  }

  if (!params.input) {
    console.error('错误：缺少 --input 参数')
    console.error('用法：node bundle.js --input <deck.html> --output <presentation.html> --skill-dir <dir>')
    process.exit(1)
  }
  if (!params.output) {
    console.error('错误：缺少 --output 参数')
    process.exit(1)
  }
  if (!params.skillDir) {
    console.error('错误：缺少 --skill-dir 参数')
    process.exit(1)
  }

  return params
}

/**
 * 将 href 解析为绝对文件路径
 * 支持绝对路径和相对路径（相对于 skill-dir 解析）
 * @param {string} href - HTML 中的 href 属性值
 * @param {string} skillDir - 技能目录绝对路径
 * @param {string} htmlDir - 输入 HTML 所在目录绝对路径
 * @returns {string} 绝对文件路径
 */
const resolveFilePath = (href, skillDir, htmlDir) => {
  // 跳过 http/https/CDN 链接
  if (/^https?:\/\//i.test(href) || href.startsWith('//')) {
    return null
  }

  // 绝对路径（以 / 开头或盘符开头）
  if (path.isAbsolute(href)) {
    return href
  }

  // 相对路径 - 先尝试相对于 HTML 目录解析
  const fromHtml = path.resolve(htmlDir, href)
  if (fs.existsSync(fromHtml)) {
    return fromHtml
  }

  // 再尝试相对于 skill-dir 解析
  const fromSkill = path.resolve(skillDir, href)
  if (fs.existsSync(fromSkill)) {
    return fromSkill
  }

  // 尝试去掉 ../ 前缀后相对于 skill-dir 解析
  const stripped = href.replace(/^(\.\.\/)+/, '')
  const fromSkillStripped = path.resolve(skillDir, stripped)
  if (fs.existsSync(fromSkillStripped)) {
    return fromSkillStripped
  }

  return null
}

/**
 * 内联所有 CSS <link> 标签
 * @param {string} html - HTML 内容
 * @param {string} skillDir - 技能目录
 * @param {string} htmlDir - HTML 所在目录
 * @returns {string} 处理后的 HTML
 */
const inlineCss = (html, skillDir, htmlDir) => {
  // 匹配 <link rel="stylesheet" href="...">
  const linkRegex = /<link\s+[^>]*?rel=["']stylesheet["'][^>]*?href=["']([^"']+)["'][^>]*?>/gi

  return html.replace(linkRegex, (match, href) => {
    const filePath = resolveFilePath(href, skillDir, htmlDir)

    if (!filePath) {
      // CDN 或无法解析的链接，保持原样
      console.log(`  跳过（外部链接）：${href}`)
      return match
    }

    try {
      const cssContent = fs.readFileSync(filePath, 'utf-8')
      console.log(`  内联 CSS：${path.relative(skillDir, filePath)}`)
      return `<style>\n${cssContent}\n</style>`
    } catch (err) {
      console.error(`  警告：无法读取 CSS 文件 ${filePath}：${err.message}`)
      return match
    }
  })
}

/**
 * 内联所有 <script src> 标签
 * @param {string} html - HTML 内容
 * @param {string} skillDir - 技能目录
 * @param {string} htmlDir - HTML 所在目录
 * @returns {string} 处理后的 HTML
 */
const inlineJs = (html, skillDir, htmlDir) => {
  // 匹配 <script src="..."></script>
  const scriptRegex = /<script\s+[^>]*?src=["']([^"']+)["'][^>]*?>\s*<\/script>/gi

  return html.replace(scriptRegex, (match, src) => {
    const filePath = resolveFilePath(src, skillDir, htmlDir)

    if (!filePath) {
      // CDN 或无法解析的链接，保持原样
      console.log(`  跳过（外部链接）：${src}`)
      return match
    }

    try {
      const jsContent = fs.readFileSync(filePath, 'utf-8')
      console.log(`  内联 JS：${path.relative(skillDir, filePath)}`)
      return `<script>\n${jsContent}\n</script>`
    } catch (err) {
      console.error(`  警告：无法读取 JS 文件 ${filePath}：${err.message}`)
      return match
    }
  })
}

/**
 * 主函数
 */
const main = () => {
  const { input, output, skillDir } = parseArgs()

  // 解析绝对路径
  const inputPath = path.resolve(input)
  const outputPath = path.resolve(output)
  const skillDirAbs = path.resolve(skillDir)
  const htmlDir = path.dirname(inputPath)

  console.log('=== html-ppt-creator 单文件打包 ===')
  console.log(`输入：${inputPath}`)
  console.log(`输出：${outputPath}`)
  console.log(`技能目录：${skillDirAbs}`)
  console.log('')

  // 检查输入文件存在
  if (!fs.existsSync(inputPath)) {
    console.error(`错误：输入文件不存在：${inputPath}`)
    process.exit(1)
  }

  // 读取 HTML
  let html = fs.readFileSync(inputPath, 'utf-8')

  // 内联 CSS
  console.log('--- 内联 CSS ---')
  html = inlineCss(html, skillDirAbs, htmlDir)

  // 内联 JS
  console.log('--- 内联 JS ---')
  html = inlineJs(html, skillDirAbs, htmlDir)

  // 写入输出文件
  const outputDir = path.dirname(outputPath)
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true })
  }
  fs.writeFileSync(outputPath, html, 'utf-8')

  // 统计输出大小
  const sizeBytes = Buffer.byteLength(html, 'utf-8')
  const sizeKB = (sizeBytes / 1024).toFixed(1)

  console.log('')
  console.log(`✓ 打包完成：${outputPath}`)
  console.log(`  文件大小：${sizeKB} KB`)
}

try {
  main()
} catch (err) {
  console.error(`打包失败：${err.message}`)
  process.exit(1)
}
