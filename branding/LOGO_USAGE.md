# PromptOps Logo Usage Guide

## Logo Files

The official PromptOps logo is located at:
- **Primary Logo**: [`promptops-logo.png`](promptops-logo.png) (2150x1984px, PNG format)
- **Distribution copies**:
  - Frontend: `frontend/dashboard/public/promptops-logo.png`
  - Assets: `assets/promptops-logo.png`
  - Branding: `branding/promptops-logo.png`

## Logo Design

The PromptOps logo features:
- **Design**: Camera aperture-style circular elements around the letter "P"
- **Colors**: Deep purple (#3d3177) as the primary brand color
- **Style**: Modern, professional, tech-focused
- **Format**: High-resolution PNG with transparency

## Usage Guidelines

### ✅ Correct Usage

1. **Web Applications**
   - Use on white or light backgrounds for best visibility
   - Maintain aspect ratio when scaling
   - Minimum size: 48x48px for UI elements
   - Recommended sizes:
     - Navigation logo: 48x48px
     - Login page: 80x80px
     - Documentation: 200-300px width

2. **Documentation**
   - Center-align in README files
   - Width: 200-300px for headers
   - Always include alt text: "PromptOps Logo"

3. **Favicon**
   - Can be used as favicon for web applications
   - Reference in HTML: `<link rel="icon" type="image/png" href="/promptops-logo.png" />`

### ❌ Incorrect Usage

- Do not stretch or distort the logo
- Do not change the logo colors
- Do not add effects (shadows, borders) unless specified by design team
- Do not place on busy backgrounds that reduce visibility
- Do not use low-resolution versions in production

## Implementation

### React/TypeScript

```tsx
<img
  src="/promptops-logo.png"
  alt="PromptOps Logo"
  style={{
    width: '48px',
    height: '48px',
    objectFit: 'contain'
  }}
/>
```

### HTML

```html
<img src="/promptops-logo.png" alt="PromptOps Logo" width="200">
```

### Markdown

```markdown
![PromptOps Logo](assets/promptops-logo.png)
```

Or centered:

```markdown
<div align="center">
  <img src="assets/promptops-logo.png" alt="PromptOps Logo" width="200"/>
</div>
```

## Brand Colors

Primary purple from the logo:
- **Hex**: `#3d3177`
- **RGB**: `rgb(61, 49, 119)`
- **Usage**: Primary brand color, backgrounds, accents

Gradient variations used in the UI:
- Sky blue to purple: `linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%)`
- Sky blue to teal: `linear-gradient(135deg, #0ea5e9 0%, #0f766e 100%)`

## File Locations

All logo files are synchronized across:
1. `branding/promptops-logo.png` - Source of truth
2. `assets/promptops-logo.png` - For documentation
3. `frontend/dashboard/public/promptops-logo.png` - For web application

## Questions?

For logo design questions or new logo variants, contact the PromptOps design team.

---

**Last Updated**: June 3, 2026  
**Version**: 1.0.0
