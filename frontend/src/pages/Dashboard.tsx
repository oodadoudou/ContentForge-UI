import React from 'react';
import { Card, Typography, Button, Space, Statistic, List } from 'antd';
import { RocketOutlined, HistoryOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/useStore';

const { Title, Paragraph } = Typography;

export const Dashboard: React.FC = () => {
    const navigate = useNavigate();
    const activeTaskId = useStore(state => state.activeTaskId);
    const updateTaskStatus = useStore(state => state.updateTaskStatus);

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Welcome to ContentForge</Title>
            <Paragraph>
                Your all-in-one desktop toolkit for content creation, organization, and ebook production.
            </Paragraph>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 24, marginTop: 32 }}>
                <Card title="System Status" bordered={false}>
                    <Statistic
                        title="Active Task"
                        value={activeTaskId ? "Running" : "Idle"}
                        valueStyle={{ color: activeTaskId ? '#3f8600' : '#cf1322' }}
                    />
                    <div style={{ marginTop: 16 }}>
                        <Button onClick={() => updateTaskStatus("Running test...")} disabled={!activeTaskId}>
                            View Logs
                        </Button>
                    </div>
                </Card>

                <Card title="Quick Actions" bordered={false}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                        <Button icon={<RocketOutlined />} block onClick={() => navigate('/downloaders')}>
                            Open Downloaders
                        </Button>
                        <Button icon={<RocketOutlined />} block onClick={() => navigate('/ebook')}>
                            Ebook Tools
                        </Button>
                    </Space>
                </Card>

                <Card title="Recent Activity" bordered={false} extra={<HistoryOutlined />}>
                    <List
                        size="small"
                        dataSource={[]}
                        renderItem={(item) => <List.Item>{item}</List.Item>}
                        locale={{ emptyText: 'No recent tasks' }}
                    />
                </Card>
            </div>
        </div>
    );
};
