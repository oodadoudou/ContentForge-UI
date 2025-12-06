import React, { useEffect, useRef, useState } from 'react';
import { Card, Button, Space } from 'antd';
import { CopyOutlined, DeleteOutlined, PauseCircleOutlined, PlayCircleOutlined, StopOutlined } from '@ant-design/icons';
import { useStore } from '../store/useStore';
import { taskApi } from '../api/tasks';
import clsx from 'clsx';
import { message } from 'antd';

export const Console: React.FC = () => {
    const logs = useStore((state) => state.logs);
    const clearLogs = useStore((state) => state.clearLogs);
    const autoScroll = useStore((state) => state.settings.auto_scroll_console);

    // Local auto-scroll toggle
    const [localAutoScroll, setLocalAutoScroll] = useState(autoScroll);
    const [inputValue, setInputValue] = useState('');
    const [isInteractive] = useState(true); // Assuming always interactive for now for input availability

    const bottomRef = useRef<HTMLDivElement>(null);
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (localAutoScroll && bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, localAutoScroll]);

    const handleCopy = () => {
        navigator.clipboard.writeText(logs.join('\n'));
    };

    const handleStop = async () => {
        try {
            await taskApi.stopTask();
            message.info("Kill signal sent.");
        } catch (e) {
            console.error("Failed to stop task", e);
            message.error("Failed to send stop signal.");
        }
    };

    const handleKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            if (!inputValue) return;
            try {
                // Optimistically show input in log
                useStore.getState().addLog(`> ${inputValue}`);
                await taskApi.sendInput(inputValue); // Ensure taskApi is imported
                setInputValue('');
            } catch (err) {
                console.error("Failed to send input", err);
            }
        }
    };

    return (
        <Card
            title="Console"
            size="small"
            extra={
                <Space>
                    <Button
                        type="text"
                        danger
                        icon={<StopOutlined />}
                        onClick={handleStop}
                        title="Force Stop Process"
                    />
                    <Button
                        type="text"
                        icon={localAutoScroll ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                        onClick={() => setLocalAutoScroll(!localAutoScroll)}
                        title={localAutoScroll ? "Pause Scrolling" : "Resume Scrolling"}
                    />
                    <Button type="text" icon={<CopyOutlined />} onClick={handleCopy} title="Copy All" />
                    <Button type="text" icon={<DeleteOutlined />} onClick={clearLogs} title="Clear" />
                </Space>
            }
            style={{ height: '300px', minHeight: '200px', resize: 'vertical', overflow: 'hidden', display: 'flex', flexDirection: 'column', border: '1px solid #303030' }}
            bodyStyle={{ flex: 1, overflow: 'hidden', padding: 0, position: 'relative', display: 'flex', flexDirection: 'column' }}
        >
            <div
                ref={scrollContainerRef}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '12px',
                    backgroundColor: '#1e1e1e',
                    color: '#d4d4d4',
                    fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
                    fontSize: '12px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all'
                }}
            >
                {logs.map((log, index) => (
                    <div key={index} className={clsx(
                        log.includes("[ERROR]") && "text-red-400",
                        log.includes("[SYSTEM]") && "text-yellow-400",
                    )}>
                        <div dangerouslySetInnerHTML={{ __html: formatLog(log) }} />
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>

            {/* Input Area - Enhanced Visibility */}
            <div style={{
                padding: '8px 12px',
                borderTop: '1px solid #333',
                background: '#2d2d2d',
                display: 'flex',
                alignItems: 'center',
                boxShadow: '0 -2px 5px rgba(0,0,0,0.2)'
            }}>
                <span style={{ color: '#52c41a', marginRight: 8, fontWeight: 'bold' }}>$</span>
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={!isInteractive}
                    placeholder="在此输入命令 (按 Enter 发送)..."
                    style={{
                        flex: 1,
                        background: 'transparent',
                        border: 'none',
                        color: '#fff',
                        fontFamily: 'Consolas, Monaco, monospace',
                        fontSize: '13px',
                        outline: 'none',
                        height: '24px'
                    }}
                    autoFocus
                />
            </div>
        </Card>
    );
};

function formatLog(log: string) {
    if (log.includes("[ERROR]")) return `<span style="color: #ff7875">${log}</span>`;
    if (log.includes("[SYSTEM]")) return `<span style="color: #faad14">${log}</span>`;
    // Basic ANSI color handling could go here if needed
    return log;
}
