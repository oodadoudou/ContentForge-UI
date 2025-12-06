import React, { useState } from 'react';
import { Card, Button, Typography, Tooltip, Row, Col, message, Modal } from 'antd';
import { FilePdfOutlined, MergeCellsOutlined, RocketOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { Title, Paragraph, Text: AntText } = Typography;

export const ComicProcessing: React.FC = () => {
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
            // Default params based on convention
            const params = {
                ...values,
                input_dir: effectiveWorkDir,
                output_dir: `${effectiveWorkDir}/processed_dir`,
                // For merge_pdfs
                output_file: `${effectiveWorkDir}/processed_dir/merged.pdf`
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

    const HelpIcon = ({ title, content }: { title: string, content: React.ReactNode }) => (
        <Tooltip title="点击查看说明" placement="top">
            <QuestionCircleOutlined
                style={{ marginLeft: 8, cursor: 'pointer', color: '#1890ff' }}
                onClick={() => Modal.info({ title, content, width: 600, maskClosable: true })}
            />
        </Tooltip>
    );

    return (
        <div style={{ padding: 24 }}>
            <Title level={2} style={{ marginBottom: 30 }}>漫画处理 (Comic Processing)</Title>
            <Paragraph>
                提供漫画图片处理、PDF 合并及智能流水线工具。请确保文件已放置在全局工作目录中。
            </Paragraph>

            <Row gutter={[16, 16]}>
                <Col span={8}>
                    <Card title={
                        <>
                            图片转 PDF
                            <HelpIcon
                                title="图片转 PDF 说明"
                                content={
                                    <Typography>
                                        <Paragraph>将工作目录下的图片文件夹转换为 PDF 文件。</Paragraph>
                                        <Paragraph>
                                            <AntText strong>目录结构要求：</AntText>
                                            <pre style={{ background: '#f5f5f5', padding: 8, marginTop: 8, borderRadius: 4 }}>
                                                WorkDir/<br />
                                                ├── Chapter1/ (包含图片 *.jpg, *.png)<br />
                                                ├── Chapter2/ (包含图片)<br />
                                                └── ...
                                            </pre>
                                            <AntText>输出：<AntText code>WorkDir/processed_dir/Chapter1.pdf</AntText></AntText>
                                        </Paragraph>
                                    </Typography>
                                }
                            />
                        </>
                    }>
                        <Button
                            type="primary"
                            icon={<FilePdfOutlined />}
                            loading={loading}
                            onClick={() => runScript('img_to_pdf')}
                        >
                            开始转换
                        </Button>
                    </Card>
                </Col>

                <Col span={8}>
                    <Card title={
                        <>
                            合并 PDF
                            <HelpIcon
                                title="合并 PDF 说明"
                                content={
                                    <Typography>
                                        <Paragraph>将工作目录下的所有 PDF 文件按照文件名顺序合并为一个文件。</Paragraph>
                                        <Paragraph>
                                            <AntText strong>目录结构要求：</AntText>
                                            <pre style={{ background: '#f5f5f5', padding: 8, marginTop: 8, borderRadius: 4 }}>
                                                WorkDir/<br />
                                                ├── 01.pdf<br />
                                                ├── 02.pdf<br />
                                                └── ...
                                            </pre>
                                            <AntText>输出：<AntText code>WorkDir/processed_dir/merged.pdf</AntText></AntText>
                                        </Paragraph>
                                    </Typography>
                                }
                            />
                        </>
                    }>
                        <Button
                            type="primary"
                            icon={<MergeCellsOutlined />}
                            loading={loading}
                            onClick={() => runScript('merge_pdfs')}
                        >
                            合并所有 PDF
                        </Button>
                    </Card>
                </Col>

                <Col span={8}>
                    <Card title={
                        <>
                            智能流水线 (V5)
                            <HelpIcon
                                title="智能流水线 V5 说明"
                                content={
                                    <Typography>
                                        <Paragraph>一站式自动化处理漫画流程：包含长图合并、智能分割、PDF 生成。</Paragraph>
                                        <Paragraph>
                                            <AntText strong>目录结构要求 (文件夹模式)：</AntText>
                                            <pre style={{ background: '#f5f5f5', padding: 8, marginTop: 8, borderRadius: 4 }}>
                                                WorkDir/<br />
                                                ├── 漫画章节A/ (包含图片)<br />
                                                ├── 漫画章节B/ (包含图片)<br />
                                                └── ...
                                            </pre>
                                        </Paragraph>
                                        <Paragraph>
                                            每个子文件夹将被视为一个独立的章节进行处理。处理完成后会自动生成对应的 PDF 文件。
                                        </Paragraph>
                                    </Typography>
                                }
                            />
                        </>
                    }>
                        <Button
                            type="primary"
                            icon={<RocketOutlined />}
                            loading={loading}
                            onClick={() => runScript('ai_pipeline_v5')}
                        >
                            运行流水线
                        </Button>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
