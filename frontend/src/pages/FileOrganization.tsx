import React, { useState } from 'react';
import { Card, Button, Typography, Tooltip, Row, Col, message, Modal, Space } from 'antd';
import { LockOutlined, UnlockOutlined, TranslationOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { taskApi } from '../api/tasks';
import { useStore } from '../store/useStore';

const { Title, Paragraph } = Typography;
const Text = Typography.Text;

export const FileOrganization: React.FC = () => {
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
                target_dir: effectiveWorkDir
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
            <Title level={2} style={{ marginBottom: 30 }}>文件整理 (File Organization)</Title>
            <Paragraph>
                提供文件整理、翻译重命名及加密工具。请确保文件已放置在全局工作目录中。
            </Paragraph>

            <Row gutter={[16, 16]}>
                <Col span={8}>
                    <Card title={
                        <>
                            翻译与整理 (AI)
                            <HelpIcon
                                title="翻译与整理说明"
                                content={
                                    <Typography>
                                        <Paragraph>整理工作目录下的文件，并使用 AI 进行翻译重命名。</Paragraph>
                                        <Paragraph>
                                            <Text strong>功能说明：</Text>
                                            <ul>
                                                <li><Text strong>一键整理 (AI):</Text> 将文件名翻译为中文或英文，并添加拼音，移动到对应的分类目录中。</li>
                                                <li><Text strong>仅整理:</Text> 仅移动文件到分类目录，不修改文件名。</li>
                                            </ul>
                                        </Paragraph>
                                    </Typography>
                                }
                            />
                        </>
                    }>
                        <Space size={[8, 8]} wrap>
                            <Button
                                type="primary"
                                icon={<TranslationOutlined />}
                                loading={loading}
                                onClick={() => runScript('translate_org', { translate: true, add_pinyin: true })}
                            >
                                一键整理 (AI 翻译)
                            </Button>
                            <Button
                                type="primary"
                                onClick={() => runScript('organize_only', { target_dir: useStore.getState().settings.workDir })}
                            >
                                仅整理 (不翻译)
                            </Button>
                        </Space>
                    </Card>
                </Col>

                <Col span={8}>
                    <Card title={
                        <>
                            文件夹加密 / 解密
                            <HelpIcon
                                title="加密/解密说明"
                                content={
                                    <Typography>
                                        <Paragraph>对工作目录下的文件夹进行 7z 加密或解密。</Paragraph>
                                        <Paragraph>
                                            <Text strong>交互说明：</Text>
                                            <p>点击按钮后，程序将在下方控制台运行。</p>
                                            <p><Text strong type="warning">请在下方控制台输入密码 (Console)。</Text></p>
                                        </Paragraph>
                                        <Paragraph>
                                            <Text type="secondary">如果不输入密码，默认使用 "1111"。</Text>
                                        </Paragraph>
                                    </Typography>
                                }
                            />
                        </>
                    }>
                        <Space size={[8, 8]} wrap>
                            <Button
                                type="primary"
                                icon={<LockOutlined />}
                                onClick={() => runScript('folder_codec', { mode: 'encrypt' })}
                            >
                                加密文件夹
                            </Button>
                            <Button
                                type="primary"
                                icon={<UnlockOutlined />}
                                onClick={() => runScript('folder_codec', { mode: 'decrypt' })}
                            >
                                解密文件夹
                            </Button>
                        </Space>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
