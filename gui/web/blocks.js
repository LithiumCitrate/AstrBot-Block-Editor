// AstrBot Block Editor - 块定义
const BLOCK_COLORS = {
    trigger: '#10b981',
    action: '#6366f1',
    logic: '#f59e0b',
    util: '#06b6d4'
};

const BLOCK_ICONS = {
    trigger: '⚡',
    action: '💬',
    logic: '🔀',
    util: '🔧'
};

const BLOCKS = {
    // 触发器
    'trigger.command': {
        type: 'trigger', category: 'trigger', name: '指令触发', color: '#10b981',
        params: [
            { name: 'command', type: 'string', label: '指令名', default: 'hello' },
            { name: 'alias', type: 'array', label: '别名', default: [] },
            { name: 'description', type: 'string', label: '描述', default: '' }
        ],
        outputs: ['flow', 'event']
    },
    'trigger.regex': {
        type: 'trigger', category: 'trigger', name: '正则触发', color: '#059669',
        params: [
            { name: 'pattern', type: 'string', label: '正则表达式', default: '^test.*' }
        ],
        outputs: ['flow', 'match']
    },
    'trigger.keyword': {
        type: 'trigger', category: 'trigger', name: '关键词触发', color: '#34d399',
        params: [
            { name: 'keywords', type: 'array', label: '关键词', default: ['你好', 'hello'] },
            { name: 'match_all', type: 'boolean', label: '全部匹配', default: false }
        ],
        outputs: ['flow', 'matched']
    },
    'trigger.permission': {
        type: 'trigger', category: 'trigger', name: '权限过滤', color: '#6ee7b7',
        params: [
            { name: 'permission', type: 'enum', label: '权限', default: 'ADMIN', options: ['ADMIN', 'MEMBER', 'OWNER'] }
        ],
        outputs: ['flow']
    },
    
    // 动作
    'action.reply_text': {
        type: 'action', category: 'action', name: '回复文本', color: '#6366f1',
        params: [
            { name: 'text', type: 'template', label: '内容', default: '你好！' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.reply_image': {
        type: 'action', category: 'action', name: '回复图片', color: '#818cf8',
        params: [
            { name: 'source_type', type: 'enum', label: '来源', default: 'url', options: ['url', 'file'] },
            { name: 'url', type: 'string', label: 'URL', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.delay': {
        type: 'action', category: 'action', name: '延迟', color: '#a78bfa',
        params: [
            { name: 'seconds', type: 'number', label: '秒数', default: 1 }
        ],
        inputs: ['flow'], outputs: ['flow']
    },
    'action.stop_event': {
        type: 'action', category: 'action', name: '停止传播', color: '#c4b5fd',
        params: [],
        inputs: ['flow'], outputs: []
    },
    'action.http_request': {
        type: 'action', category: 'action', name: 'HTTP请求', color: '#4f46e5',
        params: [
            { name: 'method', type: 'enum', label: '方法', default: 'GET', options: ['GET', 'POST', 'PUT', 'DELETE'] },
            { name: 'url', type: 'string', label: 'URL', default: '' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'response' }
        ],
        inputs: ['flow'], outputs: ['flow', 'response']
    },
    
    // 逻辑
    'logic.if': {
        type: 'logic', category: 'logic', name: '条件判断', color: '#f59e0b',
        params: [
            { name: 'condition', type: 'template', label: '条件', default: '{value} > 0' }
        ],
        inputs: ['flow'], outputs: ['flow_true', 'flow_false']
    },
    'logic.for_each': {
        type: 'logic', category: 'logic', name: '循环', color: '#fbbf24',
        params: [
            { name: 'items', type: 'string', label: '列表', default: '[]' },
            { name: 'item_var', type: 'string', label: '变量名', default: 'item' }
        ],
        inputs: ['flow'], outputs: ['flow_loop', 'flow_done']
    },
    'logic.try_catch': {
        type: 'logic', category: 'logic', name: '异常处理', color: '#fcd34d',
        params: [],
        inputs: ['flow'], outputs: ['flow_try', 'flow_catch']
    },
    
    // 工具
    'util.get_sender_info': {
        type: 'util', category: 'util', name: '发送者信息', color: '#06b6d4',
        params: [
            { name: 'info_type', type: 'enum', label: '类型', default: 'id', options: ['id', 'name', 'role'] },
            { name: 'save_to', type: 'string', label: '保存到', default: 'sender_id' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.time_now': {
        type: 'util', category: 'util', name: '当前时间', color: '#22d3ee',
        params: [
            { name: 'format', type: 'string', label: '格式', default: '%Y-%m-%d %H:%M:%S' },
            { name: 'save_to', type: 'string', label: '保存到', default: 'now' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.random': {
        type: 'util', category: 'util', name: '随机数', color: '#67e8f9',
        params: [
            { name: 'min', type: 'number', label: '最小值', default: 1 },
            { name: 'max', type: 'number', label: '最大值', default: 100 },
            { name: 'save_to', type: 'string', label: '保存到', default: 'random_num' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.variable': {
        type: 'util', category: 'util', name: '变量操作', color: '#a5f3fc',
        params: [
            { name: 'operation', type: 'enum', label: '操作', default: 'set', options: ['set', 'get', 'increment', 'decrement'] },
            { name: 'name', type: 'string', label: '变量名', default: 'counter' },
            { name: 'value', type: 'template', label: '值', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow', 'result']
    },
    'util.log': {
        type: 'util', category: 'util', name: '日志', color: '#cffafe',
        params: [
            { name: 'level', type: 'enum', label: '级别', default: 'info', options: ['debug', 'info', 'warning', 'error'] },
            { name: 'message', type: 'template', label: '消息', default: '' }
        ],
        inputs: ['flow'], outputs: ['flow']
    }
};

// 生成块卡片HTML
function generateBlockCard(blockType) {
    const block = BLOCKS[blockType];
    if (!block) return '';
    
    const paramTags = block.params.slice(0, 3).map(p => `<span class="param-tag">${p.label}</span>`).join('');
    
    return `
        <div class="block-card" data-block-type="${blockType}" style="--block-color: ${block.color}">
            <div class="block-header">
                <div class="block-icon">${BLOCK_ICONS[block.category]}</div>
                <div>
                    <div class="block-name">${block.name}</div>
                    <div class="block-type">${blockType}</div>
                </div>
            </div>
            <div class="block-params">${paramTags}</div>
        </div>
    `;
}

// 生成工作区块HTML
function generateWorkspaceBlock(blockInstance) {
    const block = BLOCKS[blockInstance.type];
    if (!block) return '';
    
    const paramsHtml = block.params.map(p => {
        const value = blockInstance.params[p.name] ?? p.default;
        const displayValue = Array.isArray(value) ? value.join(', ') : String(value);
        return `
            <div class="ws-param">
                <span class="ws-param-label">${p.label}</span>
                <span class="ws-param-value">${displayValue}</span>
            </div>
        `;
    }).join('');
    
    // 生成连接点
    const blockType = block.type;
    let connectionPointsHtml = '';
    
    // 输入点（顶部）- 非触发器块有输入点
    if (blockType !== 'trigger') {
        connectionPointsHtml += `<div class="connection-point input" title="输入端口"></div>`;
    }
    
    // 输出点（底部）
    const outputs = block.outputs || ['flow'];
    if (outputs.length > 0 && blockType !== 'util' || outputs.includes('flow')) {
        // 多输出端口时水平排列
        outputs.forEach((output, i) => {
            if (output.startsWith('flow')) {
                const offsetX = outputs.length > 1 ? (i - (outputs.length - 1) / 2) * 40 : 0;
                const color = {
                    'flow': '#6366f1',
                    'flow_true': '#10b981',
                    'flow_false': '#ef4444',
                    'flow_loop': '#f59e0b',
                    'flow_done': '#06b6d4'
                }[output] || '#6366f1';
                connectionPointsHtml += `<div class="connection-point output multi-output" style="left: calc(50% + ${offsetX}px); background: ${color};" title="${output}"></div>`;
            }
        });
    }
    
    return `
        <div class="ws-block ${blockInstance.selected ? 'selected' : ''}" 
             id="${blockInstance.id}" 
             style="left: ${blockInstance.x}px; top: ${blockInstance.y}px; --block-color: ${block.color}">
            <div class="ws-block-header">
                <div class="ws-block-icon">${BLOCK_ICONS[block.category]}</div>
                <span class="ws-block-title">${block.name}</span>
            </div>
            <div class="ws-block-content">${paramsHtml}</div>
            ${connectionPointsHtml}
        </div>
    `;
}

window.BLOCKS = BLOCKS;
window.BLOCK_COLORS = BLOCK_COLORS;
window.BLOCK_ICONS = BLOCK_ICONS;
window.generateBlockCard = generateBlockCard;
window.generateWorkspaceBlock = generateWorkspaceBlock;
