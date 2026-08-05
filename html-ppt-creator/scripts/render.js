#!/usr/bin/env node
/**
 * html-ppt-creator :: render.js
 *
 * 跨平台 PNG/PDF 渲染命令生成脚本。
 * 检测系统 Edge 浏览器路径，根据模式拼接无头浏览器命令，输出到 stdout。
 * Agent 通过 run_command 执行输出的命令。
 *
 * 用法：
 *   PNG 模式：node render.js --html <path> --mode png --slide-count N --out-dir <dir>
 *   PDF 模式：node render.js --html <path> --mode pdf --out-dir <dir>
 *
 * 依赖：Node.js 白名单模块（fs, path, os）- 零第三方依赖
 * 注意：本脚本不直接执行浏览器命令，仅输出命令字符串。
 *       Agent 用 run_command 执行（UseIO Node.js 沙箱禁止 child_process）。
 */

'use strict'

const fs = require('fs')
const path = require('path')
const os = require('os')

/**
 * 解析命令行参数
 */
const parseArgs = () => {
  const args = process.argv.slice(2)
  const params = { mode: 'png', slideCount: 1 }
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--html' && args[i + 1]) params.html = args[++i]
    else if (args[i] === '--mode' && args[i + 1]) params.mode = args[++i]
    else if (args[i] === '--slide-count' && args[i + 1]) params.slideCount = parseInt(args[++i], 10)
    else if (args[i] === '--out-dir' && args[i + 1]) params.outDir = args[++i]
  }

  if (!params.html) {
    console.error('错误：缺少 --html 参数')
    console.error('用法：node render.js --html <path> --mode <png|pdf> [--slide-count N] [--out-dir <dir>]')
    process.exit(1)
  }

  return params
}

/**
 * 检测浏览器路径（跨平台，优先 Chrome，其次 Edge）
 * @returns {{path: string, name: string}|null} 浏览器信息，未找到返回 null
 */
const detectBrowser = () => {
  const platform = os.platform()
  const candidates = []

  if (platform === 'win32') {
    // Windows - 优先 Chrome，其次 Edge
    candidates.push(
      { path: path.join('C:', 'Program Files', 'Google', 'Chrome', 'Application', 'chrome.exe'), name: 'Chrome' },
      { path: path.join('C:', 'Program Files (x86)', 'Google', 'Chrome', 'Application', 'chrome.exe'), name: 'Chrome' },
      { path: path.join('C:', 'Program Files (x86)', 'Microsoft', 'Edge', 'Application', 'msedge.exe'), name: 'Edge' },
      { path: path.join('C:', 'Program Files', 'Microsoft', 'Edge', 'Application', 'msedge.exe'), name: 'Edge' },
    )
  } else if (platform === 'darwin') {
    // macOS
    candidates.push(
      { path: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', name: 'Chrome' },
      { path: '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', name: 'Edge' },
    )
  } else {
    // Linux
    candidates.push(
      { path: '/usr/bin/google-chrome', name: 'Chrome' },
      { path: '/usr/bin/google-chrome-stable', name: 'Chrome' },
      { path: '/usr/bin/chromium', name: 'Chromium' },
      { path: '/usr/bin/chromium-browser', name: 'Chromium' },
      { path: '/usr/bin/microsoft-edge', name: 'Edge' },
      { path: '/usr/bin/microsoft-edge-stable', name: 'Edge' },
    )
  }

  for (const candidate of candidates) {
    if (fs.existsSync(candidate.path)) {
      return candidate
    }
  }

  return null
}

/**
 * 将文件路径转为 file:// URL
 */
const toFileUrl = (filePath) => {
  const abs = path.resolve(filePath).replace(/\\/g, '/')
  // Windows 盘符需要额外处理
  if (/^[A-Za-z]:/.test(abs)) {
    return 'file:///' + abs
  }
  return 'file://' + abs
}

/**
 * 生成 PNG 渲染命令
 */
const generatePngCommands = (edgePath, htmlPath, slideCount, outDir) => {
  const htmlAbs = path.resolve(htmlPath)
  const outDirAbs = path.resolve(outDir || path.dirname(htmlAbs))

  if (!fs.existsSync(outDirAbs)) {
    fs.mkdirSync(outDirAbs, { recursive: true })
  }

  const fileUrl = toFileUrl(htmlAbs)
  const stem = path.basename(htmlPath, path.extname(htmlPath))
  const commands = []

  for (let i = 1; i <= slideCount; i++) {
    const pageNum = String(i).padStart(2, '0')
    const outFile = path.join(outDirAbs, `${stem}_${pageNum}.png`)
    const url = `${fileUrl}#/${i}`

    const cmd = `"${edgePath}" --headless=new --disable-gpu --hide-scrollbars --no-sandbox --virtual-time-budget=4000 --window-size=1920,1080 --screenshot="${outFile}" "${url}"`
    commands.push(cmd)
  }

  return commands
}

/**
 * 生成 PDF 渲染命令
 */
const generatePdfCommand = (edgePath, htmlPath, outDir) => {
  const htmlAbs = path.resolve(htmlPath)
  const outDirAbs = path.resolve(outDir || path.dirname(htmlPath))

  if (!fs.existsSync(outDirAbs)) {
    fs.mkdirSync(outDirAbs, { recursive: true })
  }

  const fileUrl = toFileUrl(htmlAbs)
  const stem = path.basename(htmlPath, path.extname(htmlPath))
  const outFile = path.join(outDirAbs, `${stem}.pdf`)

  const cmd = `"${edgePath}" --headless=new --disable-gpu --no-sandbox --print-to-pdf="${outFile}" --no-pdf-header-footer "${fileUrl}"`

  return [cmd]
}

/**
 * 主函数
 */
const main = () => {
  const params = parseArgs()

  console.log('=== html-ppt-creator 渲染命令生成 ===')
  console.log(`HTML：${path.resolve(params.html)}`)
  console.log(`模式：${params.mode}`)

  // 检测浏览器（优先 Chrome，其次 Edge）
  const browser = detectBrowser()
  if (!browser) {
    console.error('')
    console.error('错误：未检测到 Chrome 或 Edge 浏览器')
    console.error('')
    console.error('请安装 Chrome 或 Edge：')
    console.error('  Chrome: https://www.google.com/chrome/')
    console.error('  Edge:   https://www.microsoft.com/edge')
    process.exit(1)
  }

  console.log(`浏览器：${browser.name} (${browser.path})`)
  console.log('')

  // 检查 HTML 文件存在
  if (!fs.existsSync(params.html)) {
    console.error(`错误：HTML 文件不存在：${params.html}`)
    process.exit(1)
  }

  // 生成命令
  let commands
  if (params.mode === 'pdf') {
    commands = generatePdfCommand(browser.path, params.html, params.outDir)
  } else {
    commands = generatePngCommands(browser.path, params.html, params.slideCount, params.outDir)
  }

  // 输出命令
  console.log(`--- 待执行命令（共 ${commands.length} 条）---`)
  console.log('')
  commands.forEach((cmd, i) => {
    console.log(`[命令 ${i + 1}/${commands.length}]`)
    console.log(cmd)
    console.log('')
  })

  console.log('请通过 run_command 逐条执行上述命令。')
}

try {
  main()
} catch (err) {
  console.error(`渲染命令生成失败：${err.message}`)
  process.exit(1)
}
