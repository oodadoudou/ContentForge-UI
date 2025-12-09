import React, { useState } from 'react';
import { Card, Button, Typography, Tooltip, Row, Col, message, Modal, Space } from 'antd';
import { FileTextOutlined, QuestionCircleOutlined, FileMarkdownOutlined } from '@ant-design/icons';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { Title, Paragraph, Text: AntText } = Typography;

export const EbookWorkshop: React.FC = () => {
    const setActiveTask = useStore(state => state.setActiveTask);
    const [loading, setLoading] = useState(false);

    const runScript = async (scriptId: string, values: any = {}) => {
        const { workDir, default_work_dir } = useStore.getState().settings;
        const effectiveWorkDir = workDir || default_work_dir;

        if (!effectiveWorkDir) {
            message.error("请先在仪表盘设置全局工作目录 (Global Working Directory)。");
            return;
        }

        setLoading(true);
        try {
            const params = {
                ...values,
                input_dir: effectiveWorkDir,
                output_dir: `${effectiveWorkDir}/processed_dir`,
            };

            const res = await taskApi.runScript(scriptId, params);
            setActiveTask(res.task_id, res.status);
            message.success("任务已启动，请查看下方控制台。");
        } catch (error) {
            console.error("Failed to run script", error);
            message.error("启动任务失败");
        } finally {
            setLoading(false);
        }
    };

    const batchToolsHelpContent = (
        <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
            <Title level={4} style={{ marginTop: 0 }}>📖 批量工具使用手册</Title>
            <Paragraph>
                提供基于规则的文本批量处理功能。程序将在您设置的<b>全局工作目录</b>中查找文件并执行操作。
            </Paragraph>

            <Title level={5}>📂 目录规范 (Directory Structure)</Title>
            <ul>
                <li><b>输入 (Input)</b>: 全局工作目录。程序会自动扫描目录下的 <code>.txt</code> 和 <code>.epub</code> 文件。</li>
                <li><b>输出 (Output)</b>: 处理后的文件将保存至 <code>processed_files</code> 子文件夹。</li>
                <li><b>报告 (Report)</b>: 详细的变更对比报告将保存至 <code>compare_reference</code> 子文件夹。</li>
            </ul>

            <Title level={5}>🛠️ 功能模块 (Modules)</Title>

            <p><b>1. 批量替换器 (Batch Replacer)</b></p>
            <p>根据指定的规则文件批量替换文本内容。</p>
            <ul>
                <li><b>规则文件识别</b>: 目录中必须包含 <code>rules.txt</code>, <code>rule.txt</code> 或 <code>规则.txt</code> 其中之一（优先级按顺序）。</li>
                <li><b>支持的规则格式</b>:
                    <ul>
                        <li><b>标准格式</b>: <code>旧文本 -&gt; 新文本 (Mode: Text)</code> <span style={{ color: '#999' }}>（支持 Text 或 Regex 模式）</span></li>
                        <li><b>静读天下导出格式</b>: <code>旧文本#-&gt;#新文本</code> <span style={{ color: '#999' }}>（运行时自动转换为标准格式）</span></li>
                    </ul>
                </li>
            </ul>

            <p><b>2. 替换模板下载 (Template Download)</b></p>
            <p>在当前工作目录生成一个包含示例文本的 <code>rules.txt</code> 模板文件。</p>

            <p><b>3. 标点修复器 (Punctuation Fixer)</b></p>
            <p>自动扫描并修复常见的中文标点误用，例如：</p>
            <ul>
                <li>修正中文字符间的半角标点。</li>
                <li>去除标点符号前多余的空格。</li>
                <li>规范化引号和括号的使用。</li>
            </ul>
        </div>
    );

    const HelpIcon = ({ title, content }: { title: string, content: React.ReactNode }) => (
        <Tooltip title="点击查看说明" placement="top">
            <QuestionCircleOutlined
                style={{ marginLeft: 8, cursor: 'pointer', color: '#1890ff' }}
                onClick={() => Modal.info({
                    title: title,
                    content: content,
                    width: 650,
                    icon: null,
                    maskClosable: true,
                    okText: "关闭"
                })}
            />
        </Tooltip>
    );

    const textConverterHelpContent = (
        <Typography>
            <Title level={5}>TXT 转 EPUB 说明</Title>
            <Paragraph>
                将 TXT 文件转换为 EPUB 格式。
            </Paragraph>
            <Paragraph>
                <AntText strong>目录识别规则：</AntText>
                <ul>
                    <li>使用 <AntText code># 标题名</AntText> 作为一级标题 (卷/章)</li>
                    <li>使用 <AntText code>## 标题名</AntText> 作为二级标题 (章/节)</li>
                </ul>
                <AntText type="warning">注意：目前仅支持 Markdown 风格的 # 标记。</AntText>
            </Paragraph>
            <Paragraph>
                如果您需要更强大的正则目录匹配或复杂排版，建议使用专门的工具如 <AntText code>Calibre</AntText> 或 <AntText code>EasyPub</AntText>。
            </Paragraph>
            <Title level={5}>其他转换说明</Title>
            <Paragraph>
                <AntText strong>Markdown 转 HTML：</AntText> 适合将排版好的 Markdown 转换为网页格式。
            </Paragraph>
            <Paragraph>
                <AntText strong>EPUB 转 TXT：</AntText> 无损提取 EPUB 中的文字内容。
            </Paragraph>
        </Typography>
    );

    const otherToolsHelpContent = (
        <Typography>
            <Paragraph>
                <AntText strong>EPUB 清理器：</AntText>
                删除 EPUB 中的冗余文件（如 iTunesMetadata.plist, ncx 等），减小体积。
            </Paragraph>
            <Paragraph>
                <AntText strong>合并与分割：</AntText>
                支持将超大 EPUB 分割为多个小卷，或将多个 EPUB 合并。
            </Paragraph>
            <Paragraph>
                <AntText strong>样式处理：</AntText>
                提取 EPUB 中的 CSS 样式表，或将预设样式应用到书籍中。
            </Paragraph>
        </Typography>
    );

    return (
        <div style={{ padding: 24 }}>
            <Title level={2} style={{ marginBottom: 30 }}>电子书工坊 (Ebook Workshop)</Title>
            <Paragraph>
                提供电子书格式转换、编辑、修复及样式处理工具。
            </Paragraph>

            {/* --- 1. 文本转换器 --- */}
            <Title level={4} style={{ marginTop: 20, marginBottom: 16 }}>1. 文本转换器</Title>
            <Row gutter={[16, 16]}>
                <Col span={8}>
                    <Card title={<>TXT 转 EPUB <HelpIcon title="文本转换器说明" content={textConverterHelpContent} /></>}>
                        <Button type="primary" icon={<FileTextOutlined />} loading={loading} onClick={() => runScript('txt_to_epub')}>
                            TXT 转 EPUB
                        </Button>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card title={<>Markdown 转 HTML <HelpIcon title="文本转换器说明" content={textConverterHelpContent} /></>}>
                        <Button type="primary" icon={<FileMarkdownOutlined />} loading={loading} onClick={() => runScript('md_to_html')}>
                            Markdown 转 HTML
                        </Button>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card title={<>EPUB 转 TXT <HelpIcon title="文本转换器说明" content={textConverterHelpContent} /></>}>
                        <Button type="primary" icon={<FileTextOutlined />} loading={loading} onClick={() => runScript('epub_to_txt')}>
                            EPUB 转 TXT
                        </Button>
                    </Card>
                </Col>
            </Row>

            {/* --- 2. 批量工具 --- */}
            <Title level={4} style={{ marginTop: 30, marginBottom: 16 }}>2. 批量工具</Title>
            <Row gutter={[16, 16]}>
                <Col span={24}>
                    <Card title={<>批量工具集 <HelpIcon title="批量工具说明" content={batchToolsHelpContent} /></>}>
                        <Space size={[8, 8]} wrap>
                            <Button type="primary" onClick={() => runScript('batch_replacer')}>批量替换器</Button>
                            <Button type="primary" onClick={() => runScript('download_rules')}>替换模板下载</Button>
                            <Button type="primary" onClick={() => runScript('punctuation_fixer')}>标点修复器</Button>
                        </Space>
                    </Card>
                </Col>
            </Row>

            {/* --- 3. 其他 EPUB 工具 --- */}
            <Title level={4} style={{ marginTop: 30, marginBottom: 16 }}>3. 其他 EPUB 工具</Title>
            <Row gutter={[16, 16]}>
                <Col span={12}>
                    <Card title={<>文件修复与清理 <HelpIcon title="其他工具说明" content={otherToolsHelpContent} /></>}>
                        <Space size={[8, 8]} wrap>
                            <Button type="primary" onClick={() => runScript('epub_cleaner')}>EPUB 清理器</Button>
                            <Button type="primary" onClick={() => runScript('fix_txt_encoding')}>修复 TXT 编码</Button>
                            <Button type="primary" onClick={() => runScript('cover_repair')}>修复封面</Button>
                        </Space>
                    </Card>
                </Col>
                <Col span={6}>
                    <Card title={<>合并与分割 <HelpIcon title="其他工具说明" content={otherToolsHelpContent} /></>}>
                        <Space size={[8, 8]} wrap>
                            <Button type="primary" onClick={() => runScript('split_epub')}>分割 EPUB</Button>
                        </Space>
                    </Card>
                </Col>
                <Col span={6}>
                    <Card title={<>样式处理 <HelpIcon title="其他工具说明" content={otherToolsHelpContent} /></>}>
                        <Space size={[8, 8]} wrap>
                            <Button type="primary" onClick={() => runScript('extract_css')}>提取 CSS</Button>
                            <Button type="primary" onClick={() => runScript('epub_styler')}>应用样式 (Styler)</Button>
                        </Space>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
