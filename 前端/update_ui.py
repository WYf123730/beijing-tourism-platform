import os

css_path = r"C:\Users\Administrator\Desktop\北京市旅游信息服务平台\前端\css\style.css"

with open(css_path, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Floating sidebar
old = "#sidePanel {\n    width: var(--panel-width);\n    min-width: var(--panel-width);\n    background: var(--card);\n    border-right: 1px solid var(--border);\n    overflow-y: auto;\n    z-index: 100;\n    box-shadow: 2px 0 8px rgba(0,0,0,0.05);\n}"
new = "#sidePanel {\n    width: var(--panel-width);\n    min-width: var(--panel-width);\n    background: rgba(255,255,255,0.88);\n    backdrop-filter: blur(16px);\n    -webkit-backdrop-filter: blur(16px);\n    border-right: none;\n    border-radius: 0 16px 16px 0;\n    margin: 8px 0 8px 8px;\n    height: calc(100% - 16px);\n    overflow-y: auto;\n    z-index: 100;\n    box-shadow: 0 8px 32px rgba(0,0,0,0.12);\n    transition: all 0.3s ease;\n}"
c = c.replace(old, new)

# 2. Glass result items
old = ".result-item {\n    background: white;\n    border: 1px solid var(--border);\n    border-radius: 6px;\n    padding: 10px;\n    margin: 6px 0;\n    transition: var(--transition);\n    cursor: pointer;\n}\n\n.result-item:hover {\n    box-shadow: var(--shadow);\n    border-color: var(--primary);\n}"
new = ".result-item {\n    background: rgba(255,255,255,0.9);\n    backdrop-filter: blur(4px);\n    border: 1px solid rgba(218,220,224,0.5);\n    border-radius: 8px;\n    padding: 10px 12px;\n    margin: 6px 0;\n    transition: all 0.25s ease;\n    cursor: pointer;\n}\n\n.result-item:hover {\n    box-shadow: 0 4px 12px rgba(26,115,232,0.12);\n    border-color: var(--primary);\n    transform: translateY(-1px);\n}"
c = c.replace(old, new)

# 3. Weather gradient
old = ".weather-info {\n    text-align: center;\n    padding: 16px;\n    background: linear-gradient(135deg, #e3f2fd, #bbdefb);\n    border-radius: var(--radius);\n    margin-bottom: 12px;\n}"
new = ".weather-info {\n    text-align: center;\n    padding: 20px;\n    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n    border-radius: 12px;\n    margin-bottom: 12px;\n    color: white;\n    box-shadow: 0 4px 16px rgba(102,126,234,0.3);\n}"
c = c.replace(old, new)

# 4. Weather main text colors
old = ".weather-main {\n    font-size: 36px;\n    font-weight: 700;\n    color: var(--primary);\n}"
new = ".weather-main {\n    font-size: 42px;\n    font-weight: 700;\n    color: white;\n    text-shadow: 0 2px 8px rgba(0,0,0,0.15);\n}"
c = c.replace(old, new)

old = ".weather-desc {\n    font-size: 16px;\n    color: var(--text);\n    margin: 4px 0;\n}"
new = ".weather-desc {\n    font-size: 18px;\n    color: rgba(255,255,255,0.9);\n    margin: 4px 0;\n}"
c = c.replace(old, new)

old = ".weather-detail {\n    font-size: 13px;\n    color: var(--text-secondary);\n    display: flex;\n    justify-content: center;\n    gap: 16px;\n    margin-top: 8px;\n}"
new = ".weather-detail {\n    font-size: 13px;\n    color: rgba(255,255,255,0.75);\n    display: flex;\n    justify-content: center;\n    gap: 16px;\n    margin-top: 8px;\n}"
c = c.replace(old, new)

# 5. Tool buttons
old = ".tool-btn {\n    background: var(--primary);\n    color: white;\n    border: none;\n    padding: 8px 14px;\n    border-radius: 6px;\n    cursor: pointer;\n    font-size: 13px;\n    font-weight: 500;\n    transition: var(--transition);\n    margin: 4px;\n}\n\n.tool-btn:hover {\n    background: var(--primary-dark);\n    transform: translateY(-1px);\n    box-shadow: var(--shadow);\n}"
new = ".tool-btn {\n    background: var(--primary);\n    color: white;\n    border: none;\n    padding: 8px 16px;\n    border-radius: 8px;\n    cursor: pointer;\n    font-size: 13px;\n    font-weight: 500;\n    transition: all 0.25s ease;\n    margin: 3px;\n    box-shadow: 0 2px 6px rgba(26,115,232,0.2);\n}\n\n.tool-btn:hover {\n    background: var(--primary-dark);\n    transform: translateY(-2px);\n    box-shadow: 0 4px 12px rgba(26,115,232,0.3);\n}"
c = c.replace(old, new)

# 6. Map tip
old = ".map-tip {\n    position: absolute;\n    top: 16px;\n    right: 16px;\n    background: rgba(255,255,255,0.95);\n    padding: 8px 16px;\n    border-radius: 20px;\n    box-shadow: var(--shadow-lg);\n    font-size: 13px;\n    color: var(--text-secondary);\n    z-index: 99;\n    pointer-events: none;\n}"
new = ".map-tip {\n    position: absolute;\n    top: 16px;\n    right: 16px;\n    background: rgba(255,255,255,0.9);\n    backdrop-filter: blur(8px);\n    padding: 8px 20px;\n    border-radius: 20px;\n    box-shadow: 0 4px 20px rgba(0,0,0,0.1);\n    border: 1px solid rgba(255,255,255,0.3);\n    font-size: 13px;\n    color: var(--text-secondary);\n    z-index: 99;\n    pointer-events: none;\n}"
c = c.replace(old, new)

# 7. Input focus
old = ".search-box input {\n    flex: 1;\n    padding: 8px 12px;\n    border: 1px solid var(--border);\n    border-radius: 6px;\n    font-size: 14px;\n    outline: none;\n    transition: var(--transition);\n}\n\n.search-box input:focus {\n    border-color: var(--primary);\n    box-shadow: 0 0 0 2px rgba(26,115,232,0.2);\n}"
new = ".search-box input {\n    flex: 1;\n    padding: 10px 14px;\n    border: 1px solid rgba(218,220,224,0.5);\n    border-radius: 8px;\n    font-size: 14px;\n    outline: none;\n    background: rgba(255,255,255,0.85);\n    transition: all 0.25s ease;\n}\n\n.search-box input:focus {\n    border-color: var(--primary);\n    box-shadow: 0 0 0 3px rgba(26,115,232,0.15);\n    background: white;\n}"
c = c.replace(old, new)

# 8. Info box
old = ".info-box {\n    background: var(--primary-light);\n    padding: 10px;\n    border-radius: 6px;\n    font-size: 13px;\n    color: var(--text-secondary);\n}"
new = ".info-box {\n    background: rgba(232,240,254,0.7);\n    backdrop-filter: blur(4px);\n    padding: 10px 14px;\n    border-radius: 8px;\n    font-size: 13px;\n    color: var(--text-secondary);\n    border: 1px solid rgba(255,255,255,0.3);\n}"
c = c.replace(old, new)

# 9. Tool group
old = ".tool-group {\n    margin-bottom: 16px;\n    padding: 12px;\n    background: var(--bg);\n    border-radius: var(--radius);\n}"
new = ".tool-group {\n    margin-bottom: 16px;\n    padding: 12px;\n    background: rgba(245,247,250,0.7);\n    border-radius: var(--radius);\n    border: 1px solid rgba(255,255,255,0.6);\n}"
c = c.replace(old, new)

# 10. Nav header gradient
old = "#header {\n    height: var(--nav-height);\n    background: linear-gradient(135deg, #1a73e8, #1557b0);\n    color: white;"
new = "#header {\n    height: var(--nav-height);\n    background: linear-gradient(135deg, #1a73e8 0%, #1557b0 50%, #0d47a1 100%);\n    color: white;"
c = c.replace(old, new)

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(c)
print('CSS floating style applied')
