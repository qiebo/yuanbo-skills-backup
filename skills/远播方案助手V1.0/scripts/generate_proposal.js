'use strict';

/*
 * 教育项目方案Word文档生成模板
 * 基于 Node.js + docx 库
 *
 * 使用方法（两种模式）：
 *
 * 模式A - 直接编辑（快速原型）：
 *   1. 修改下方 "文档配置区" 的元数据
 *   2. 在 "内容填充区" 按章节填写正文
 *   3. 执行: node generate_proposal.js
 *
 * 模式B - 从Markdown读取（推荐用于迭代）：
 *   1. 将 `3_方案终稿.md` 放在同一目录
 *   2. 修改 CONFIG 中的 markdownSource 指向该文件
 *   3. 执行: node generate_proposal.js
 *   脚本会自动解析Markdown标题和段落，生成对应Word结构
 *
 * 编码规范：
 *   - 所有中文字符串使用 Unicode 转义（如 \u5B8B\u4F53 = 宋体）
 *   - 中文引号使用 \u201c / \u201d
 *   - 破折号使用 \u2014
 *   - 单引号使用 \u2018 / \u2019
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, TableOfContents,
  LevelFormat
} = require('docx');
const fs = require('fs');

// ==================== 文档配置区 ====================
const CONFIG = {
  // 封面信息
  coverTitle: '\u6E56\u5DDE\u4E2D\u5B66\u8111\u673A\u63A5\u53E3\u5B9E\u9A8C\u5BA4\u5EFA\u8BBE\u9879\u76EE\u7533\u62A5\u65B9\u6848', // 文档标题
  coverSchool: '\u6E56\u5DDE\u4E2D\u5B66', // 学校名称
  coverDate: '2026\u5E744\u6708', // 日期

  // 输出文件名
  outputFile: './\u65B9\u6848\u6587\u6863.docx',

  // 页眉文字
  headerText: '\u6E56\u5DDE\u4E2D\u5B66\u8111\u673A\u63A5\u53E3\u5B9E\u9A8C\u5BA4\u5EFA\u8BBE\u9879\u76EE\u7533\u62A5\u65B9\u6848',

  // 字体（默认宋体）
  font: '\u5B8B\u4F53',

  // Markdown源文件路径（模式B使用，设为null则使用模式A直接填充）
  markdownSource: null, // 示例: './3_\u65B9\u6848\u7EC8\u7A3F.md'
};

// ==================== Helper函数 ====================

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, bold: true, size: 32, font: CONFIG.font })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, size: 28, font: CONFIG.font })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, size: 24, font: CONFIG.font })]
  });
}

function p(text, opts) {
  const runs = [];
  if (typeof text === 'string') {
    runs.push(new TextRun({ text, size: 24, font: CONFIG.font }));
  } else {
    runs.push(...text);
  }
  return new Paragraph({
    spacing: { before: 60, after: 60, line: 360 },
    ...opts,
    children: runs
  });
}

function p_mixed(parts) {
  const runs = parts.map(part => {
    if (typeof part === 'string') {
      return new TextRun({ text: part, size: 24, font: CONFIG.font });
    }
    return new TextRun({ text: part.text, bold: part.bold, size: 24, font: CONFIG.font, ...part });
  });
  return new Paragraph({ spacing: { before: 60, after: 60, line: 360 }, children: runs });
}

function center(text, size, bold) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 120 },
    children: [new TextRun({ text, size: size || 24, bold: bold || false, font: CONFIG.font })]
  });
}

function makeTable(headers, rows, colWidths) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: 'AAAAAA' };
  const borders = { top: border, bottom: border, left: border, right: border };

  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: 'D0E8F8', type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: h, bold: true, size: 22, font: CONFIG.font })]
      })]
    }))
  });

  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        children: [new TextRun({ text: cell, size: 22, font: CONFIG.font })]
      })]
    }))
  }));

  return new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE }
  });
}

// ==================== 内容填充区 ====================

// 第一章 项目背景与意义
function chapter1() {
  return [
    h1('\u7B2C\u4E00\u7AE0 \u9879\u76EE\u80CC\u666F\u4E0E\u610F\u4E49'),
    h2('1.1 \u653F\u7B56\u80CC\u666F'),
    p('\u5728\u6B64\u586B\u5199\u653F\u7B56\u80CC\u666F\u5185\u5BB9\u3002\u5F15\u7528\u5177\u4F53\u653F\u7B56\u6587\u4EF6\u540D\u79F0\u548C\u6587\u53F7\uFF0C\u8BF4\u660E\u56FD\u5BB6\u6216\u5730\u65B9\u5BF9\u8BE5\u9886\u57DF\u7684\u652F\u6301\u65B9\u5411\u3002'),
    h2('1.2 \u5B66\u6821\u73B0\u72B6\u4E0E\u9700\u6C42\u5206\u6790'),
    p('\u5728\u6B64\u586B\u5199\u5B66\u6821\u73B0\u72B6\u5206\u6790\u3002\u5305\u62EC\u5B66\u6821\u5B9A\u4F4D\u3001\u73B0\u6709\u57FA\u7840\u3001\u5B58\u5728\u7684\u5DEE\u8DDD\u4E0E\u9700\u6C42\u3002'),
    h2('1.3 \u9879\u76EE\u5EFA\u8BBE\u610F\u4E49'),
    p('\u5728\u6B64\u586B\u5199\u5EFA\u8BBE\u610F\u4E49\u3002\u4ECE\u5B66\u751F\u53D1\u5C55\u3001\u6559\u5E08\u6210\u957F\u3001\u5B66\u6821\u53D1\u5C55\u4E09\u4E2A\u5C42\u9762\u9610\u8FF0\uFF0C\u907F\u514D\u7A7A\u6D1E\u63CF\u8FF0\u3002'),
  ];
}

// 第二章 建设目标与主要内容
function chapter2() {
  return [
    h1('\u7B2C\u4E8C\u7AE0 \u5EFA\u8BBE\u76EE\u6807\u4E0E\u4E3B\u8981\u5185\u5BB9'),
    h2('2.1 \u5EFA\u8BBE\u76EE\u6807'),
    p('\u5728\u6B64\u586B\u5199\u5EFA\u8BBE\u76EE\u6807\u3002\u7528\u5177\u4F53\u3001\u53EF\u8861\u91CF\u7684\u6307\u6807\u63CF\u8FF0\uFF0C\u907F\u514D\u7A7A\u6CDB\u8868\u8FBE\u3002'),
    h2('2.2 \u4E3B\u8981\u5EFA\u8BBE\u5185\u5BB9'),
    p('\u5728\u6B64\u586B\u5199\u4E3B\u8981\u5EFA\u8BBE\u5185\u5BB9\u6982\u8FF0\u3002\u4ECB\u7ECD\u5EFA\u8BBE\u7684\u6838\u5FC3\u65B9\u5411\u4E0E\u91CD\u70B9\uFF0C\u4E0D\u5C55\u5F00\u8FC7\u591A\u6280\u672F\u7EC6\u8282\u3002'),
  ];
}

// 第三章 建设方案
function chapter3() {
  return [
    h1('\u7B2C\u4E09\u7AE0 \u5EFA\u8BBE\u65B9\u6848'),
    h2('3.1 \u603B\u4F53\u8BBE\u8BA1\u601D\u8DEF'),
    p('\u5728\u6B64\u586B\u5199\u603B\u4F53\u8BBE\u8BA1\u601D\u8DEF\u3002\u5305\u62EC\u6280\u672F\u8DEF\u7EBF\u3001\u529F\u80FD\u5B9A\u4F4D\u3001\u8BBE\u8BA1\u539F\u5219\u7B49\u3002'),
    h2('3.2 \u7A7A\u95F4\u5E03\u5C40\u4E0E\u529F\u80FD\u5206\u533A'),
    p('\u5728\u6B64\u586B\u5199\u7A7A\u95F4\u5E03\u5C40\u65B9\u6848\u3002\u63CF\u8FF0\u5404\u529F\u80FD\u533A\u57DF\u7684\u5206\u5E03\u4E0E\u9762\u79EF\u89C4\u5212\u3002'),
    h2('3.3 \u8BBE\u5907\u914D\u7F6E\u4E0E\u6280\u672F\u53C2\u6570'),
    p('\u5728\u6B64\u586B\u5199\u8BBE\u5907\u914D\u7F6E\u65B9\u6848\u3002\u53EF\u4EE5\u4F7F\u7528\u4E0B\u65B9\u7684\u8BBE\u5907\u914D\u7F6E\u8868\u6A21\u677F\uFF0C\u6216\u7528\u6BB5\u843D\u63CF\u8FF0\u3002'),
    // 设备配置表示例
    makeTable(
      ['\u5E8F\u53F7', '\u8BBE\u5907\u540D\u79F0', '\u89C4\u683C/\u578B\u53F7', '\u5355\u4F4D', '\u6570\u91CF', '\u5355\u4EF7(\u4E07\u5143)', '\u5408\u8BA1(\u4E07\u5143)'],
      [
        ['1', '\u793A\u4F8B\u8BBE\u5907A', '\u4E13\u4E1A\u7EA7', '\u53F0', '1', '50.00', '50.00'],
        ['2', '\u793A\u4F8B\u8BBE\u5907B', '\u6807\u914D\u7248', '\u5957', '2', '15.00', '30.00'],
      ],
      [500, 1800, 1800, 600, 600, 1200, 1200]
    ),
  ];
}

// 第四章 课程与教学体系
function chapter4() {
  return [
    h1('\u7B2C\u56DB\u7AE0 \u8BFE\u7A0B\u4E0E\u6559\u5B66\u4F53\u7CFB\u5EFA\u8BBE'),
    h2('4.1 \u8BFE\u7A0B\u8BBE\u8BA1\u7406\u5FF5'),
    p('\u5728\u6B64\u586B\u5199\u8BFE\u7A0B\u8BBE\u8BA1\u7406\u5FF5\u3002\u4ECB\u7ECD\u8BFE\u7A0B\u67B6\u6784\u4E0E\u80FD\u529B\u57F9\u517B\u76EE\u6807\u3002'),
    h2('4.2 \u8BFE\u7A0B\u5185\u5BB9\u6846\u67B6'),
    p('\u5728\u6B64\u586B\u5199\u8BFE\u7A0B\u5185\u5BB9\u6846\u67B6\u3002\u63CF\u8FF0\u5404\u6A21\u5757\u7684\u5185\u5BB9\u4E0E\u5B66\u65F6\u5B89\u6392\u3002'),
    h2('4.3 \u6559\u5B66\u5B9E\u65BD\u4E0E\u8BC4\u4EF7'),
    p('\u5728\u6B64\u586B\u5199\u6559\u5B66\u5B9E\u65BD\u65B9\u6848\u4E0E\u8BC4\u4EF7\u4F53\u7CFB\u3002'),
  ];
}

// 第五章 经费预算
function chapter5() {
  return [
    h1('\u7B2C\u4E94\u7AE0 \u7ECF\u8D39\u9884\u7B97\u4E0E\u8D44\u91D1\u6765\u6E90'),
    h2('5.1 \u7ECF\u8D39\u9884\u7B97\u603B\u8868'),
    p('\u5728\u6B64\u586B\u5199\u9884\u7B97\u603B\u4F53\u8BF4\u660E\u3002\u5305\u62EC\u603B\u91D1\u989D\u3001\u5404\u7C7B\u8D39\u7528\u5360\u6BD4\u3001\u8D44\u91D1\u6765\u6E90\u7B49\u3002'),
    // 预算总表示例
    makeTable(
      ['\u5E8F\u53F7', '\u8D39\u7528\u7C7B\u522B', '\u91D1\u989D(\u4E07\u5143)', '\u5360\u6BD4', '\u5907\u6CE8'],
      [
        ['1', '\u8BBE\u5907\u8D2D\u7F6E\u8D39', '242.00', '78%', '\u542B\u5B9E\u9A8C\u8BBE\u5907\u4E0E\u8F6F\u4EF6\u5E73\u53F0'],
        ['2', '\u88C5\u4FEE\u6539\u9020\u8D39', '37.00', '12%', '\u5B9E\u9A8C\u5BA4\u73AF\u5883\u6539\u9020'],
        ['3', '\u8BFE\u7A0B\u5F00\u53D1\u4E0E\u5E08\u8D44\u57F9\u8BAD\u8D39', '31.00', '10%', '\u542B\u6559\u6750\u7F16\u5199\u4E0E\u57F9\u8BAD'],
        ['\u5408\u8BA1', '', '310.00', '100%', ''],
      ],
      [500, 1800, 1200, 800, 2200]
    ),
    h2('5.2 \u8D44\u91D1\u6765\u6E90'),
    p('\u5728\u6B64\u586B\u5199\u8D44\u91D1\u6765\u6E90\u8BF4\u660E\u3002\u660E\u786E\u5404\u6E20\u9053\u7684\u91D1\u989D\u4E0E\u5360\u6BD4\u3002'),
  ];
}

// 第六章 预期成效与保障
function chapter6() {
  return [
    h1('\u7B2C\u516D\u7AE0 \u9884\u671F\u6210\u6548\u4E0E\u4FDD\u969C\u63AA\u65BD'),
    h2('6.1 \u9884\u671F\u6210\u6548'),
    p('\u5728\u6B64\u586B\u5199\u9884\u671F\u6210\u6548\u3002\u4ECB\u7ECD\u5B66\u751F\u57F9\u517B\u3001\u6559\u5E08\u53D1\u5C55\u3001\u5B66\u6821\u54C1\u724C\u7B49\u65B9\u9762\u7684\u9884\u671F\u6210\u679C\u3002\u7ADE\u8D5B\u6210\u679C\u4EC5\u6982\u8FF0\u65B9\u5411\u4E0E\u5C42\u7EA7\uFF0C\u4E0D\u5217\u4E3E\u5177\u4F53\u8D5B\u9879\u540D\u79F0\u3002'),
    h2('6.2 \u7EC4\u7EC7\u4FDD\u969C'),
    p('\u5728\u6B64\u586B\u5199\u7EC4\u7EC7\u4FDD\u969C\u63AA\u65BD\u3002\u5305\u62EC\u7EC4\u7EC7\u67B6\u6784\u3001\u7BA1\u7406\u673A\u5236\u3001\u8FDB\u5EA6\u5B89\u6392\u7B49\u3002'),
    h2('6.3 \u5236\u5EA6\u4E0E\u8FD0\u884C\u4FDD\u969C'),
    p('\u5728\u6B64\u586B\u5199\u5236\u5EA6\u4E0E\u8FD0\u884C\u4FDD\u969C\u3002'),
  ];
}

// ==================== Markdown解析器（模式B）====================

function parseMarkdown(mdPath) {
  const content = fs.readFileSync(mdPath, 'utf-8');
  const lines = content.split('\n');
  const elements = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // 标题解析
    if (trimmed.startsWith('# ')) {
      elements.push({ type: 'h1', text: trimmed.slice(2) });
    } else if (trimmed.startsWith('## ')) {
      elements.push({ type: 'h2', text: trimmed.slice(3) });
    } else if (trimmed.startsWith('### ')) {
      elements.push({ type: 'h3', text: trimmed.slice(4) });
    } else if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      // 表格行跳过（表格需要单独处理）
      continue;
    } else {
      // 普通段落
      elements.push({ type: 'p', text: trimmed });
    }
  }

  return elements;
}

function buildFromMarkdown(elements) {
  const children = [];
  for (const el of elements) {
    switch (el.type) {
      case 'h1': children.push(h1(el.text)); break;
      case 'h2': children.push(h2(el.text)); break;
      case 'h3': children.push(h3(el.text)); break;
      case 'p': children.push(p(el.text)); break;
    }
  }
  return children;
}

// ==================== 文档组装 ====================

let bodyChildren;

if (CONFIG.markdownSource && fs.existsSync(CONFIG.markdownSource)) {
  // 模式B：从Markdown读取
  console.log('\u4ECEMarkdown\u8BFB\u53D6: ' + CONFIG.markdownSource);
  const elements = parseMarkdown(CONFIG.markdownSource);
  bodyChildren = buildFromMarkdown(elements);
} else {
  // 模式A：直接填充
  bodyChildren = [
    ...chapter1(),
    ...chapter2(),
    ...chapter3(),
    ...chapter4(),
    ...chapter5(),
    ...chapter6(),
  ];
}

const children = [
  // 封面
  new Paragraph({ spacing: { before: 1200 } }),
  center(CONFIG.coverTitle, 44, true),
  new Paragraph({ spacing: { before: 800 } }),
  center(CONFIG.coverSchool, 28, false),
  center(CONFIG.coverDate, 24, false),
  new PageBreak(),

  // 目录
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 400, after: 400 },
    children: [new TextRun({ text: '\u76EE\u5F55', bold: true, size: 32, font: CONFIG.font })]
  }),
  new TableOfContents('\u76EE\u5F55', {
    hyperlink: true,
    headingStyleRange: '1-3',
    stylesWithLevels: [
      { styleId: 'Heading1', level: 0 },
      { styleId: 'Heading2', level: 1 },
      { styleId: 'Heading3', level: 2 }
    ]
  }),
  new PageBreak(),

  // 正文
  ...bodyChildren,
];

const doc = new Document({
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: CONFIG.headerText, size: 18, color: '666666', font: CONFIG.font })]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: '\u7B2C ', size: 20, font: CONFIG.font }),
              new TextRun({ children: [PageNumber.CURRENT], size: 20, font: CONFIG.font }),
              new TextRun({ text: ' \u9875', size: 20, font: CONFIG.font })
            ]
          })
        ]
      })
    },
    children,
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(CONFIG.outputFile, buffer);
  console.log('\u6587\u6863\u751F\u6210\u5B8C\u6BD5: ' + CONFIG.outputFile);
});
