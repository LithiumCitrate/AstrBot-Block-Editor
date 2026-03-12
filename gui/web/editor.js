// AstrBot Block Editor - 主编辑器逻辑
class BlockEditor {
    constructor() {
        this.blocks = [];
        this.connections = [];
        this.handlers = [{ id: 'handler_1', name: 'Handler 1' }];
        this.currentHandler = 0;
        this.selectedBlock = null;
        this.draggedBlock = null;
        this.dragOffset = { x: 0, y: 0 };
        this.blockIdCounter = 0;
        
        // 撤销/重做
        this.history = [];
        this.historyIndex = -1;
        this.maxHistory = 50;
        
        this.workspace = document.getElementById('workspace');
        this.workspaceBlocks = document.getElementById('workspaceBlocks');
        this.connectionsGroup = document.getElementById('connectionsGroup');
        
        this.init();
    }
    
    init() {
        this.loadBlocksPanel('trigger');
        this.setupEventListeners();
        this.updateHandlerTabs();
        this.checkFirstVisit();
    }
    
    // 检查是否首次访问
    checkFirstVisit() {
        const visited = localStorage.getItem('blockEditorVisited');
        if (!visited) {
            // 首次访问，显示引导
            document.getElementById('welcomeModal').style.display = 'flex';
        } else {
            document.getElementById('welcomeModal').style.display = 'none';
        }
    }
    
    // 保存状态到历史
    saveState() {
        const state = {
            blocks: JSON.parse(JSON.stringify(this.blocks)),
            connections: JSON.parse(JSON.stringify(this.connections)),
            blockIdCounter: this.blockIdCounter
        };
        
        // 移除当前位置之后的历史
        this.history = this.history.slice(0, this.historyIndex + 1);
        this.history.push(state);
        
        // 限制历史长度
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }
    }
    
    // 撤销
    undo() {
        if (this.historyIndex < 0) {
            this.showToast('没有可撤销的操作', 'warning');
            return;
        }
        
        const state = this.history[this.historyIndex];
        this.historyIndex--;
        
        this.restoreState(state);
        this.showToast('已撤销');
    }
    
    // 重做
    redo() {
        if (this.historyIndex >= this.history.length - 1) {
            this.showToast('没有可重做的操作', 'warning');
            return;
        }
        
        this.historyIndex++;
        const state = this.history[this.historyIndex];
        
        this.restoreState(state);
        this.showToast('已重做');
    }
    
    // 恢复状态
    restoreState(state) {
        this.blocks = JSON.parse(JSON.stringify(state.blocks));
        this.connections = JSON.parse(JSON.stringify(state.connections));
        this.blockIdCounter = state.blockIdCounter;
        
        // 重新渲染
        this.workspaceBlocks.innerHTML = '';
        this.blocks.forEach(b => this.renderBlock(b));
        this.updateConnections();
        this.updateBlockCount();
        this.selectBlock(null);
        
        if (this.blocks.length === 0) {
            this.showEmptyState();
        } else {
            this.hideEmptyState();
        }
    }
    
    // 显示提示
    showToast(message, type = 'info') {
        // 移除旧的toast
        document.querySelectorAll('.error-toast').forEach(t => t.remove());
        
        const toast = document.createElement('div');
        toast.className = `error-toast ${type === 'warning' ? 'warning-toast' : ''}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 2000);
    }
    
    // 验证工作流
    validate() {
        const errors = [];
        
        // 检查是否有触发器
        const triggers = this.blocks.filter(b => BLOCKS[b.type].type === 'trigger');
        if (triggers.length === 0 && this.blocks.length > 0) {
            errors.push('缺少触发器：请添加一个触发器块（绿色）');
        }
        
        // 检查是否有未连接的块
        const connectedIds = new Set();
        this.connections.forEach(c => {
            connectedIds.add(c.from);
            connectedIds.add(c.to);
        });
        
        const unconnectedBlocks = this.blocks.filter(b => 
            BLOCKS[b.type].type !== 'trigger' && !connectedIds.has(b.id)
        );
        
        if (unconnectedBlocks.length > 0) {
            errors.push(`有 ${unconnectedBlocks.length} 个块未连接`);
        }
        
        // 检查必填参数
        this.blocks.forEach(b => {
            const blockDef = BLOCKS[b.type];
            blockDef.params.forEach(p => {
                if (p.required && !b.params[p.name]) {
                    errors.push(`块「${blockDef.name}」缺少参数：${p.label}`);
                }
            });
        });
        
        // 显示错误
        const errorStatus = document.getElementById('errorStatus');
        const errorMsg = document.getElementById('errorMsg');
        
        if (errors.length > 0) {
            errorStatus.style.display = 'flex';
            errorMsg.textContent = errors[0];
            this.showToast(errors[0], 'error');
        } else {
            errorStatus.style.display = 'none';
        }
        
        return errors.length === 0;
    }
    
    loadBlocksPanel(category) {
        const container = document.getElementById('blocksContainer');
        container.innerHTML = '';
        
        document.querySelectorAll('.pill').forEach(pill => {
            pill.classList.toggle('active', pill.dataset.category === category);
        });
        
        for (const [blockType, block] of Object.entries(BLOCKS)) {
            if (block.category !== category) continue;
            container.innerHTML += generateBlockCard(blockType);
        }
        
        // 添加拖拽事件
        container.querySelectorAll('.block-card').forEach(card => {
            card.addEventListener('mousedown', (e) => this.startDragNew(e, card.dataset.blockType));
            card.addEventListener('dblclick', () => this.addBlockToWorkspace(card.dataset.blockType, 100, 100));
        });
    }
    
    setupEventListeners() {
        // 分类切换
        document.querySelectorAll('.pill').forEach(pill => {
            pill.addEventListener('click', () => this.loadBlocksPanel(pill.dataset.category));
        });
        
        // 工作区拖放
        this.workspace.addEventListener('mousemove', (e) => this.handleDrag(e));
        this.workspace.addEventListener('mouseup', () => this.endDrag());
        this.workspace.addEventListener('mouseleave', () => this.endDrag());
        
        // 点击空白取消选择
        this.workspace.addEventListener('click', (e) => {
            if (e.target === this.workspace || e.target.classList.contains('workspace-grid')) {
                this.selectBlock(null);
            }
        });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            // 删除
            if ((e.key === 'Delete' || e.key === 'Backspace') && this.selectedBlock) {
                e.preventDefault();
                this.deleteBlock(this.selectedBlock);
            }
            // 撤销 Ctrl+Z
            if (e.ctrlKey && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.undo();
            }
            // 重做 Ctrl+Y 或 Ctrl+Shift+Z
            if ((e.ctrlKey && e.key === 'y') || (e.ctrlKey && e.shiftKey && e.key === 'z')) {
                e.preventDefault();
                this.redo();
            }
            // 复制块 Ctrl+C
            if (e.ctrlKey && e.key === 'c' && this.selectedBlock) {
                e.preventDefault();
                this.copiedBlock = this.selectedBlock;
                this.showToast('块已复制');
            }
            // 粘贴块 Ctrl+V
            if (e.ctrlKey && e.key === 'v' && this.copiedBlock) {
                e.preventDefault();
                const b = this.copiedBlock;
                this.addBlockToWorkspace(b.type, b.x + 30, b.y + 30);
                // 复制参数
                const newBlock = this.blocks[this.blocks.length - 1];
                newBlock.params = JSON.parse(JSON.stringify(b.params));
                this.updateBlockDisplay(newBlock);
            }
        });
    }
    
    startDragNew(e, blockType) {
        e.preventDefault();
        this.draggedBlock = { type: 'new', blockType };
        this.dragOffset = { x: 110, y: 20 };
    }
    
    startDragExisting(e, blockInstance) {
        e.preventDefault();
        e.stopPropagation();
        this.draggedBlock = { type: 'existing', block: blockInstance };
        
        const rect = document.getElementById(blockInstance.id).getBoundingClientRect();
        const workspaceRect = this.workspace.getBoundingClientRect();
        this.dragOffset = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        
        document.getElementById(blockInstance.id).classList.add('dragging');
        this.selectBlock(blockInstance);
    }
    
    handleDrag(e) {
        if (!this.draggedBlock) return;
        
        const rect = this.workspace.getBoundingClientRect();
        const x = e.clientX - rect.left - this.dragOffset.x;
        const y = e.clientY - rect.top - this.dragOffset.y;
        
        if (this.draggedBlock.type === 'new') {
            // 预览新块位置
        } else if (this.draggedBlock.type === 'existing') {
            const block = this.draggedBlock.block;
            block.x = Math.max(0, x);
            block.y = Math.max(0, y);
            
            const el = document.getElementById(block.id);
            el.style.left = block.x + 'px';
            el.style.top = block.y + 'px';
            
            // 高亮可连接的块
            this.highlightConnectableBlocks(block);
            
            this.updateConnections();
        }
    }
    
    // 高亮可连接的块
    highlightConnectableBlocks(movingBlock) {
        // 移除所有高亮
        document.querySelectorAll('.ws-block.can-connect').forEach(el => {
            el.classList.remove('can-connect');
        });
        
        const movingBlockDef = BLOCKS[movingBlock.type];
        if (movingBlockDef.type === 'trigger') return; // 触发器不需要连接
        
        const SNAP = 50; // 扩大检测范围
        
        for (const other of this.blocks) {
            if (other.id === movingBlock.id) continue;
            
            const otherBlockDef = BLOCKS[other.type];
            
            // 检查是否可以连接到这个块的输出
            const expectedY = other.y + other.height + 10;
            if (Math.abs(movingBlock.y - expectedY) < SNAP) {
                const outputs = otherBlockDef.outputs || ['flow'];
                outputs.forEach((output, i) => {
                    if (output.startsWith('flow')) {
                        const offsetX = outputs.length > 1 ? (i - (outputs.length - 1) / 2) * 40 : 0;
                        if (Math.abs(movingBlock.x - (other.x + offsetX)) < SNAP) {
                            document.getElementById(other.id)?.classList.add('can-connect');
                        }
                    }
                });
            }
        }
    }
    
    endDrag() {
        // 清除高亮
        document.querySelectorAll('.ws-block.can-connect').forEach(el => {
            el.classList.remove('can-connect');
        });
        
        if (this.draggedBlock?.type === 'new') {
            const rect = this.workspace.getBoundingClientRect();
            const x = rect.width / 2 - 110;
            const y = 50;
            this.addBlockToWorkspace(this.draggedBlock.blockType, x, y);
        }
        
        if (this.draggedBlock?.type === 'existing') {
            document.getElementById(this.draggedBlock.block.id)?.classList.remove('dragging');
            this.snapBlock(this.draggedBlock.block);
        }
        
        this.draggedBlock = null;
    }
    
    addBlockToWorkspace(blockType, x, y) {
        const block = BLOCKS[blockType];
        if (!block) return;
        
        this.saveState();
        
        this.blockIdCounter++;
        const instance = {
            id: `block_${this.blockIdCounter}`,
            type: blockType,
            params: {},
            x: Math.max(0, x),
            y: Math.max(0, y),
            width: 220,
            height: 80 + block.params.length * 32
        };
        
        block.params.forEach(p => instance.params[p.name] = p.default);
        
        this.blocks.push(instance);
        this.renderBlock(instance);
        this.selectBlock(instance);
        this.updateBlockCount();
        this.hideEmptyState();
        this.validate();
    }
    
    renderBlock(instance) {
        this.workspaceBlocks.innerHTML += generateWorkspaceBlock(instance);
        
        const el = document.getElementById(instance.id);
        el.addEventListener('mousedown', (e) => this.startDragExisting(e, instance));
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectBlock(instance);
        });
    }
    
    selectBlock(instance) {
        document.querySelectorAll('.ws-block').forEach(el => el.classList.remove('selected'));
        this.selectedBlock = instance;
        
        if (instance) {
            document.getElementById(instance.id)?.classList.add('selected');
            this.showProperties(instance);
        } else {
            this.hideProperties();
        }
    }
    
    showProperties(instance) {
        const block = BLOCKS[instance.type];
        const panel = document.getElementById('propertiesContent');
        
        let html = `<div style="margin-bottom: 12px; font-weight: 600; color: ${block.color};">${block.name}</div>`;
        
        block.params.forEach(p => {
            const value = instance.params[p.name] ?? p.default;
            
            if (p.type === 'boolean') {
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <select class="prop-select" onchange="editor.updateParam('${instance.id}', '${p.name}', this.value === 'true')">
                        <option value="true" ${value === true ? 'selected' : ''}>是</option>
                        <option value="false" ${value === false ? 'selected' : ''}>否</option>
                    </select>
                </div>`;
            } else if (p.type === 'enum') {
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <select class="prop-select" onchange="editor.updateParam('${instance.id}', '${p.name}', this.value)">
                        ${p.options.map(opt => `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                    </select>
                </div>`;
            } else if (p.type === 'array') {
                const display = Array.isArray(value) ? value.join(', ') : '';
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <input type="text" class="prop-input" value="${display}" placeholder="逗号分隔" 
                        onchange="editor.updateParam('${instance.id}', '${p.name}', this.value.split(',').map(s=>s.trim()).filter(s=>s))">
                </div>`;
            } else {
                html += `<div class="prop-group">
                    <label class="prop-label">${p.label}</label>
                    <input type="${p.type === 'number' ? 'number' : 'text'}" class="prop-input" 
                        value="${value ?? ''}" onchange="editor.updateParam('${instance.id}', '${p.name}', this.value)">
                </div>`;
            }
        });
        
        html += `<button class="btn btn-delete" onclick="editor.deleteBlock(editor.selectedBlock)">🗑️ 删除此块</button>`;
        panel.innerHTML = html;
    }
    
    hideProperties() {
        document.getElementById('propertiesContent').innerHTML = 
            '<div style="text-align: center; color: var(--text-muted); padding: 20px 0;">选择块查看属性</div>';
    }
    
    updateParam(blockId, paramName, value) {
        const instance = this.blocks.find(b => b.id === blockId);
        if (!instance) return;
        
        instance.params[paramName] = value;
        
        // 更新显示
        const el = document.getElementById(blockId);
        el.outerHTML = generateWorkspaceBlock(instance);
        
        const newEl = document.getElementById(blockId);
        newEl.addEventListener('mousedown', (e) => this.startDragExisting(e, instance));
        newEl.addEventListener('click', (e) => { e.stopPropagation(); this.selectBlock(instance); });
        if (this.selectedBlock?.id === blockId) {
            newEl.classList.add('selected');
        }
    }
    
    // 更新块显示
    updateBlockDisplay(instance) {
        const el = document.getElementById(instance.id);
        if (el) {
            el.outerHTML = generateWorkspaceBlock(instance);
            const newEl = document.getElementById(instance.id);
            newEl.addEventListener('mousedown', (e) => this.startDragExisting(e, instance));
            newEl.addEventListener('click', (e) => { e.stopPropagation(); this.selectBlock(instance); });
        }
    }
    
    deleteBlock(instance) {
        if (!instance) return;
        
        this.saveState();
        
        this.connections = this.connections.filter(c => c.from !== instance.id && c.to !== instance.id);
        this.blocks = this.blocks.filter(b => b.id !== instance.id);
        document.getElementById(instance.id)?.remove();
        
        this.selectBlock(null);
        this.updateConnections();
        this.updateBlockCount();
        this.validate();
        
        if (this.blocks.length === 0) this.showEmptyState();
    }
    
    snapBlock(instance) {
        const SNAP = 30;
        const block = BLOCKS[instance.type];
        
        for (const other of this.blocks) {
            if (other.id === instance.id) continue;
            if (block.type === 'trigger') continue;
            
            const otherBlock = BLOCKS[other.type];
            const outputs = otherBlock.outputs || ['flow'];
            
            // 检查每个输出端口
            for (let i = 0; i < outputs.length; i++) {
                const outputName = outputs[i];
                const offsetX = i * 60 - (outputs.length - 1) * 30; // 多端口水平偏移
                
                if (Math.abs(instance.x - (other.x + offsetX)) < SNAP) {
                    const expectedY = other.y + other.height + 10;
                    if (Math.abs(instance.y - expectedY) < SNAP) {
                        instance.x = other.x + offsetX;
                        instance.y = expectedY;
                        
                        // 移除该输入端口的旧连接
                        this.connections = this.connections.filter(c => c.to !== instance.id);
                        
                        // 创建新连接，记录输出端口
                        this.connections.push({ 
                            from: other.id, 
                            to: instance.id, 
                            outputPort: outputName 
                        });
                        break;
                    }
                }
            }
        }
        
        const el = document.getElementById(instance.id);
        el.style.left = instance.x + 'px';
        el.style.top = instance.y + 'px';
        this.updateConnections();
    }
    
    updateConnections() {
        this.connectionsGroup.innerHTML = '';
        
        for (const conn of this.connections) {
            const from = this.blocks.find(b => b.id === conn.from);
            const to = this.blocks.find(b => b.id === conn.to);
            if (!from || !to) continue;
            
            const fromBlock = BLOCKS[from.type];
            const outputs = fromBlock.outputs || ['flow'];
            const portIndex = outputs.indexOf(conn.outputPort) || 0;
            
            // 计算输出端口位置
            const portOffsetX = portIndex * 60 - (outputs.length - 1) * 30;
            const x1 = from.x + 110 + portOffsetX, y1 = from.y + from.height;
            const x2 = to.x + 110, y2 = to.y;
            const midY = (y1 + y2) / 2;
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `M ${x1} ${y1} C ${x1} ${midY} ${x2} ${midY} ${x2} ${y2}`);
            path.setAttribute('class', 'connection-line');
            
            // 根据输出端口类型设置颜色
            const colors = {
                'flow': '#6366f1',
                'flow_true': '#10b981',
                'flow_false': '#ef4444',
                'flow_loop': '#f59e0b',
                'flow_done': '#06b6d4',
                'flow_try': '#10b981',
                'flow_catch': '#ef4444'
            };
            path.style.stroke = colors[conn.outputPort] || '#6366f1';
            
            this.connectionsGroup.appendChild(path);
        }
    }
    
    updateBlockCount() {
        document.getElementById('blockCount').textContent = this.blocks.length;
    }
    
    hideEmptyState() { document.getElementById('emptyState').style.display = 'none'; }
    showEmptyState() { document.getElementById('emptyState').style.display = 'block'; }
    
    addHandler() {
        const id = `handler_${this.handlers.length + 1}`;
        this.handlers.push({ id, name: `Handler ${this.handlers.length + 1}` });
        this.currentHandler = this.handlers.length - 1;
        this.updateHandlerTabs();
    }
    
    switchHandler(idx) {
        this.currentHandler = idx;
        this.updateHandlerTabs();
    }
    
    updateHandlerTabs() {
        document.getElementById('handlerTabs').innerHTML = this.handlers.map((h, i) =>
            `<div class="handler-tab ${i === this.currentHandler ? 'active' : ''}" onclick="editor.switchHandler(${i})">${h.name}</div>`
        ).join('');
        document.getElementById('handlerCount').textContent = this.handlers.length;
    }
    
    buildWorkflowJSON() {
        const triggers = this.blocks.filter(b => BLOCKS[b.type].type === 'trigger');
        const handlers = [];
        
        const buildFlow = (blockId) => {
            const flow = [];
            const conns = this.connections.filter(c => c.from === blockId);
            
            for (const conn of conns) {
                const block = this.blocks.find(b => b.id === conn.to);
                if (block) {
                    const blockDef = BLOCKS[block.type];
                    const flowItem = {
                        id: block.id,
                        block: block.type,
                        params: block.params
                    };
                    
                    // 递归处理子流程
                    if (blockDef.type === 'logic') {
                        // 逻辑块需要处理多个分支
                        const branches = {};
                        const outputs = blockDef.outputs || [];
                        for (const output of outputs) {
                            const subFlow = this.buildFlowRecursive(block.id, output, buildFlow);
                            if (subFlow.length > 0) {
                                branches[output] = subFlow;
                            }
                        }
                        if (Object.keys(branches).length > 0) {
                            flowItem.branches = branches;
                        }
                    } else {
                        // 普通块继续向下查找
                        const nextFlow = buildFlow(block.id);
                        if (nextFlow.length > 0) {
                            flowItem.flow = nextFlow;
                        }
                    }
                    
                    flow.push(flowItem);
                }
            }
            return flow;
        };
        
        triggers.forEach(trigger => {
            const flow = buildFlow(trigger.id);
            handlers.push({
                id: `handler_${handlers.length + 1}`,
                trigger: { block: trigger.type, params: trigger.params },
                flow: flow
            });
        });
        
        return {
            metadata: {
                name: document.getElementById('pluginName').value || 'my_plugin',
                author: document.getElementById('pluginAuthor').value || 'user',
                description: '',
                version: '1.0.0'
            },
            variables: [],
            handlers
        };
    }
    
    buildFlowRecursive(blockId, outputPort, buildFlowFn) {
        const flow = [];
        const conns = this.connections.filter(c => c.from === blockId && c.outputPort === outputPort);
        
        for (const conn of conns) {
            const block = this.blocks.find(b => b.id === conn.to);
            if (block) {
                const blockDef = BLOCKS[block.type];
                const flowItem = {
                    id: block.id,
                    block: block.type,
                    params: block.params
                };
                
                const nextFlow = buildFlowFn(block.id);
                if (nextFlow.length > 0) {
                    flowItem.flow = nextFlow;
                }
                
                flow.push(flowItem);
            }
        }
        return flow;
    }
    
    getConnectedBlocks(startId, outputPort = null) {
        const result = [];
        
        // 查找从指定输出端口连接的块
        const conns = this.connections.filter(c => c.from === startId && (outputPort === null || c.outputPort === outputPort));
        
        for (const conn of conns) {
            const block = this.blocks.find(b => b.id === conn.to);
            if (block && BLOCKS[block.type].type !== 'trigger') {
                result.push({
                    block: block,
                    outputPort: conn.outputPort
                });
            }
        }
        
        return result;
    }
    
    compileCode() {
        if (!this.validate()) {
            document.getElementById('codeContent').textContent = '# 请先修复错误';
            return;
        }
        
        const workflow = this.buildWorkflowJSON();
        
        if (window.pybridge) {
            const result = JSON.parse(window.pybridge.compile(JSON.stringify(workflow)));
            document.getElementById('codeContent').textContent = result.success ? result.code : '# 错误:\n' + result.errors.join('\n');
        } else {
            document.getElementById('codeContent').textContent = this.generateMockCode(workflow);
        }
    }
    
    // 加载模板
    loadTemplate(templateName) {
        const templates = {
            hello: {
                metadata: { name: 'hello_plugin', author: 'user', version: '1.0.0' },
                blocks: [
                    { type: 'trigger.command', x: 100, y: 50, params: { command: 'hello', alias: ['hi'] } },
                    { type: 'action.reply_text', x: 100, y: 150, params: { text: '你好，{sender_name}！' } }
                ],
                connections: [{ from: 'block_1', to: 'block_2', outputPort: 'flow' }]
            },
            dice: {
                metadata: { name: 'dice_game', author: 'user', version: '1.0.0' },
                blocks: [
                    { type: 'trigger.command', x: 100, y: 50, params: { command: 'dice' } },
                    { type: 'util.random', x: 100, y: 150, params: { min: 1, max: 6, save_to: 'dice_result' } },
                    { type: 'action.reply_text', x: 100, y: 250, params: { text: '🎲 骰子结果: {dice_result}' } }
                ],
                connections: [{ from: 'block_1', to: 'block_2', outputPort: 'flow' }, { from: 'block_2', to: 'block_3', outputPort: 'flow' }]
            },
            welcome: {
                metadata: { name: 'welcome_bot', author: 'user', version: '1.0.0' },
                blocks: [
                    { type: 'trigger.keyword', x: 100, y: 50, params: { keywords: ['欢迎', 'welcome'] } },
                    { type: 'action.reply_text', x: 100, y: 150, params: { text: '欢迎 {sender_name} 加入群聊！' } }
                ],
                connections: [{ from: 'block_1', to: 'block_2', outputPort: 'flow' }]
            },
            empty: {
                metadata: { name: 'my_plugin', author: 'user', version: '1.0.0' },
                blocks: [],
                connections: []
            }
        };
        
        const template = templates[templateName];
        if (!template) return;
        
        // 清空当前
        this.blocks = [];
        this.connections = [];
        this.workspaceBlocks.innerHTML = '';
        this.connectionsGroup.innerHTML = '';
        
        // 重置块ID计数器
        this.blockIdCounter = 0;
        
        // 设置元数据
        document.getElementById('pluginName').value = template.metadata.name;
        document.getElementById('pluginAuthor').value = template.metadata.author;
        
        // 加载块
        template.blocks.forEach((b, i) => {
            this.blockIdCounter++;
            const instance = {
                id: `block_${this.blockIdCounter}`,
                type: b.type,
                params: b.params,
                x: b.x,
                y: b.y,
                width: 220,
                height: 80 + BLOCKS[b.type].params.length * 32
            };
            this.blocks.push(instance);
            this.renderBlock(instance);
        });
        
        // 加载连接
        this.connections = template.connections.map(c => ({ ...c }));
        
        this.updateConnections();
        this.updateBlockCount();
        this.hideEmptyState();
        this.saveState();
        
        if (templateName !== 'empty') {
            this.showToast('模板加载成功！');
        }
    }
    
    generateMockCode(wf) {
        let code = `# ${wf.metadata.name}\nfrom astrbot.api.event import AstrMessageEvent, filter\nfrom astrbot.api import star\n\n`;
        code += `class ${this.toPascal(wf.metadata.name)}(star.Star):\n    def __init__(self, ctx):\n        self.ctx = ctx\n\n`;
        
        for (const h of wf.handlers) {
            code += `    @filter.command("${h.trigger.params.command || 'cmd'}")\n    async def ${h.id}(self, e):\n`;
            for (const b of h.flow) {
                if (b.block === 'action.reply_text') code += `        yield e.plain_result(f"${b.params.text || ''}")\n`;
                else if (b.block === 'action.delay') code += `        await asyncio.sleep(${b.params.seconds || 1})\n`;
            }
            code += '\n';
        }
        return code + '    async def terminate(self): pass\n';
    }
    
    toPascal(s) { return s.replace(/(^|[-_])(\w)/g, (_, __, c) => c.toUpperCase()); }
    
    // 加载工作流（从JSON文件）
    loadWorkflow(workflow) {
        if (!workflow || !workflow.metadata) {
            this.showToast('无效的工作流文件', 'error');
            return;
        }
        
        // 清空当前
        this.blocks = [];
        this.connections = [];
        this.workspaceBlocks.innerHTML = '';
        this.connectionsGroup.innerHTML = '';
        this.blockIdCounter = 0;
        
        // 设置元数据
        document.getElementById('pluginName').value = workflow.metadata.name || 'my_plugin';
        document.getElementById('pluginAuthor').value = workflow.metadata.author || 'user';
        
        // 加载变量
        if (workflow.variables) {
            // TODO: 处理变量
        }
        
        // 加载handlers中的块
        if (workflow.handlers) {
            workflow.handlers.forEach(handler => {
                // 加载触发器
                if (handler.trigger) {
                    this.blockIdCounter++;
                    const triggerInstance = {
                        id: `block_${this.blockIdCounter}`,
                        type: handler.trigger.block,
                        params: handler.trigger.params || {},
                        x: 100,
                        y: 50,
                        width: 220,
                        height: 80 + (BLOCKS[handler.trigger.block]?.params?.length || 0) * 32
                    };
                    this.blocks.push(triggerInstance);
                    this.renderBlock(triggerInstance);
                    
                    // 递归加载flow
                    this.loadFlowBlocks(handler.flow, triggerInstance.id);
                }
            });
        }
        
        this.updateConnections();
        this.updateBlockCount();
        this.hideEmptyState();
        this.saveState();
        this.showToast('工作流加载成功！');
    }
    
    // 递归加载flow块
    loadFlowBlocks(flow, parentId, outputPort = 'flow') {
        if (!flow || !Array.isArray(flow)) return;
        
        flow.forEach(item => {
            this.blockIdCounter++;
            const instance = {
                id: `block_${this.blockIdCounter}`,
                type: item.block,
                params: item.params || {},
                x: 100,
                y: this.blocks.length * 100 + 50,
                width: 220,
                height: 80 + (BLOCKS[item.block]?.params?.length || 0) * 32
            };
            this.blocks.push(instance);
            this.renderBlock(instance);
            
            // 创建连接
            this.connections.push({
                from: parentId,
                to: instance.id,
                outputPort: outputPort
            });
            
            // 处理子flow
            if (item.flow && Array.isArray(item.flow)) {
                this.loadFlowBlocks(item.flow, instance.id, 'flow');
            }
            
            // 处理branches（逻辑块）
            if (item.branches) {
                Object.entries(item.branches).forEach(([port, branchFlow]) => {
                    this.loadFlowBlocks(branchFlow, instance.id, port);
                });
            }
        });
    }
}

// 全局函数
function newProject() {
    if (confirm('确定新建？当前工作将丢失。')) {
        editor.blocks = []; editor.connections = []; editor.blockIdCounter = 0;
        document.getElementById('workspaceBlocks').innerHTML = '';
        document.getElementById('connectionsGroup').innerHTML = '';
        editor.selectBlock(null); editor.updateBlockCount(); editor.showEmptyState();
        document.getElementById('codeContent').textContent = '# 点击"编译预览"生成代码';
    }
}

function saveProject() {
    const json = JSON.stringify(editor.buildWorkflowJSON(), null, 2);
    if (window.pybridge) {
        window.pybridge.save(json);
    } else {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
        a.download = (document.getElementById('pluginName').value || 'workflow') + '.json';
        a.click();
    }
}

function openProject() {
    if (window.pybridge) {
        const json = window.pybridge.open();
        if (json) editor.loadWorkflow(JSON.parse(json));
    } else {
        const input = document.createElement('input');
        input.type = 'file'; input.accept = '.json';
        input.onchange = e => {
            const reader = new FileReader();
            reader.onload = e => {
                try { editor.loadWorkflow(JSON.parse(e.target.result)); } catch (err) { alert('文件格式错误'); }
            };
            reader.readAsText(e.target.files[0]);
        };
        input.click();
    }
}

function compileCode() { editor.compileCode(); }

function copyCode() {
    navigator.clipboard.writeText(document.getElementById('codeContent').textContent);
}

function exportPlugin() {
    if (window.pybridge) {
        window.pybridge.export(JSON.stringify(editor.buildWorkflowJSON()));
    } else {
        alert('请在桌面应用中使用此功能');
    }
}

function addHandler() { editor.addHandler(); }

// 显示教程
function showTutorial() {
    document.getElementById('welcomeModal').style.display = 'flex';
}

// 关闭欢迎弹窗
function closeWelcomeModal() {
    document.getElementById('welcomeModal').style.display = 'none';
    localStorage.setItem('blockEditorVisited', 'true');
}

// 选择模板
function selectTemplate(name, event) {
    document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('selected');
    }
    editor.loadTemplate(name);
    closeWelcomeModal();
}

// 搜索块
function filterBlocks(query) {
    const container = document.getElementById('blocksContainer');
    const cards = container.querySelectorAll('.block-card');
    const q = query.toLowerCase();
    
    cards.forEach(card => {
        const name = card.querySelector('.block-name').textContent.toLowerCase();
        const type = card.querySelector('.block-type').textContent.toLowerCase();
        const visible = name.includes(q) || type.includes(q);
        card.style.display = visible ? '' : 'none';
    });
}

const editor = new BlockEditor();
