# Hyu Multiverse Homepage & Dashboard Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform "Hyu Multiverse" into a stylish, bespoke, and professional entertainment archive by building a dedicated Homepage/Dashboard Portal, integrating real-time system stats, dimension portal navigation, feature highlights, spotlight carousels, and polishing visual typography and layout.

**Architecture:** Extend the single-page application in `index.html` to support a primary `home` route/state alongside existing repository states (`manhua_review`, `manhua_short`, `ggggg`, `gggg_short`, `truyen_tranh`). The homepage dynamically renders aggregate metrics from Firebase/local cache, portal cards leading into each dimension, a feature capability matrix, and curated spotlight items. Refactor global CSS design tokens to remove generic AI tropes (neon border bloat, excessive emojis) and replace them with high-end obsidian dark aesthetics, hairline borders, and crisp SVG iconography.

**Tech Stack:** Vanilla JavaScript (ES6+), HTML5, CSS3 with modern CSS custom properties and backdrop-filter, Firebase Realtime Database SDK (compat v9), YouTube Iframe Embed API.

**Spec:** User prompt requirements and approved Dashboard Portal layout:
- Dedicated Homepage view (`switchRepo('home')`) with brand identity.
- Real-time dynamic stats counter (+2,825 items, total watch duration, 5 dimensions, cloud live indicator).
- 5 Dimension Portal Cards routing directly to specific repos with item counts.
- Dashboard Feature Highlights section (Deep duration filtering, Cinema mode, Personalized library, Cloud sync).
- Spotlight section featuring top epic works (Võ Luyện Đỉnh Phong, Lookism, Ta Là Tà Đế, Đại Quản Gia Ma Hoàng).
- Clean, bespoke, non-generic professional aesthetic (no garish neon/emoji slop).

## Global Constraints
- Must NOT break Firebase Realtime Database cloud synchronization or data integrity.
- Must preserve all 2,825+ items across the 5 existing repositories.
- Must preserve AniList comic search, favorite categorization, and custom category creation.
- Single-page application must load smoothly without external framework overhead.
- Fully responsive on mobile, tablet, and desktop viewports.

## Review Focus
- Switching back and forth between "Trang Chủ" (home) and repository views must reset search/filter states cleanly without DOM memory leaks or broken event listeners.
- Cloud Realtime Database updates from Firebase must update both the Homepage stats and repository badges dynamically.
- Mobile bottom navigation and mobile drawer must navigate smoothly to Trang Chủ and all repos without layout jitter.
- Cards in the spotlight section must open the Cinema Player modal or Comic modal reliably.
- Search hotkey (`/`) or search input when on Trang Chủ should seamlessly transition to the appropriate repository or global search.

---

### Task 1: Refactor CSS Design Tokens & Base Aesthetic

**Files:**
- Modify: `/home/huyquang/Desktop/website_truyen/index.html:10-150`

**Interfaces:**
- Consumes: Existing CSS variables in `:root`
- Produces: Polished design tokens for obsidian dark background, subtle hairline borders, ambient lighting, refined typography, and removal of gaudy neon box-shadows.

- [ ] **Step 1: Inspect and update `:root` variables in `index.html`**
  - Update `--bg-base: #07090e`, `--bg-surface: #0d111d`, `--border-subtle: rgba(255, 255, 255, 0.07)`, `--border-accent: rgba(56, 189, 248, 0.3)`.
  - Add typography variables and smooth transition utilities.

- [ ] **Step 2: Clean up card styles and badges**
  - Replace rainbow neon glow (`box-shadow: 0 0 20px ...`) with smooth, natural multi-layer elevation (`box-shadow: 0 12px 32px -8px rgba(0, 0, 0, 0.75)`).
  - Standardize badge typography with crisp font sizes, letter spacing, and clean borders.

- [ ] **Step 3: Verify CSS changes in browser**
  - Verify that the card layout and sidebar render cleanly without broken styles or overflow issues.

- [ ] **Step 4: Commit**
  ```bash
  git add index.html
  git commit -m "style: upgrade design tokens to polished obsidian dark aesthetic"
  ```

---

### Task 2: Build Homepage (Trang Chủ) Layout & Dimension Portals

**Files:**
- Modify: `/home/huyquang/Desktop/website_truyen/index.html` (HTML structure & JS render logic)

**Interfaces:**
- Consumes: `repoMeta`, `getRepoData()`, `favorites`, `cloudDb`
- Produces: `renderHomePage()` function and dynamic portal cards for 5 dimensions.

- [ ] **Step 1: Add "Trang Chủ" navigation item to Sidebar & Mobile bar**
  - Add `#nav-home` with click handler `switchRepo('home')` as the primary menu item.
  - Update mobile top bar & bottom bar to highlight "Trang Chủ".

- [ ] **Step 2: Implement `renderHomePage()` in JavaScript**
  - Calculate real-time aggregate statistics across all 5 repos:
    - Total items count (2,825+)
    - Total duration in hours (+25.000h)
    - Total comics and total videos
    - Favorite count
  - Construct Hero Welcome Section:
    - Grand title: "HYU MULTIVERSE"
    - Tagline: "Đại Kho Lưu Trữ Giải Trí & Truyện Tranh Đa Vũ Trụ"
    - 4 Live Stat Cards (Tác Phẩm, Thời Lượng, Chiều Không Gian, Cloud Status)
  - Construct Dimension Portals Grid:
    - 5 interactive cards linking to each repo (`manhua_review`, `manhua_short`, `ggggg`, `gggg_short`, `truyen_tranh`).
    - Each portal displays item count, distinctive icon, tag description, and a direct "Khám Phá" button.

- [ ] **Step 3: Integrate `home` case in `switchRepo()`**
  - When `repoKey === 'home'`, hide the repository filter hub (search/sort/channel dropdowns) and render the comprehensive Homepage view inside `#contentDisplayArea`.
  - When switching to any repository, render that repository's controls and card grid.

- [ ] **Step 4: Verify navigation flow**
  - Verify clicking "Trang Chủ" shows the dashboard.
  - Verify clicking any Dimension Portal navigates directly to that repository.

- [ ] **Step 5: Commit**
  ```bash
  git add index.html
  git commit -m "feat: implement interactive Homepage and Dimension Portals in Hyu Multiverse"
  ```

---

### Task 3: Build Dashboard Features Matrix & Spotlight Heavyweights

**Files:**
- Modify: `/home/huyquang/Desktop/website_truyen/index.html`

**Interfaces:**
- Consumes: `openVideoModal()`, `openComicModal()`, `getRepoData()`
- Produces: Feature capability grid and curated Spotlight Carousel inside `renderHomePage()`.

- [ ] **Step 1: Implement Dashboard Feature Highlights Section**
  - Create a 4-column feature matrix:
    1. ⏱ **Bộ Lọc Thời Lượng Siêu Cấp**: Tự động lọc các bộ review siêu dài >50h, 30-50h.
    2. 🎬 **Cinema Player Mode**: Xem video rạp chiếu không quảng cáo, ambient lighting.
    3. ❤️ **Tủ Sách Phân Loại Đa Mục**: Tự phân chia Tu Tiên, Mạt Thế, Ngự Thú, Trọng Sinh...
    4. ☁️ **Cloud Realtime Database**: Tự động đồng bộ đa thiết bị tức thì qua Firebase.

- [ ] **Step 2: Implement Spotlight Section (Siêu Phẩm Trấn Kho)**
  - Pick 4 top landmark works:
    - "Võ Luyện Đỉnh Phong | 120 Giờ | Trọn Bộ 01-2257"
    - "Lookism | Siêu Phẩm 96H | Từ Học Sinh Béo Đến Ông Trùm"
    - "Ta Là Tà Đế | FULL BỘ END | Tạ Diệm Vạn Giới Vô Địch"
    - "Đại Quản Gia Là Ma Hoàng | 3.790 Chap | Magic Emperor"
  - Render high-impact spotlight cards with direct "Xem Phim" and "Đọc Truyện" click triggers.

- [ ] **Step 3: Test modal triggers from Spotlight cards**
  - Verify clicking a video spotlight opens `openVideoModal()` with the correct video ID, duration, and thumbnail.
  - Verify clicking a comic spotlight opens `openComicModal()`.

- [ ] **Step 4: Commit**
  ```bash
  git add index.html
  git commit -m "feat: add Dashboard Feature Matrix and Spotlight Heavyweights to Homepage"
  ```

---

### Task 4: Mobile Polish, Bottom Navigation Bar & Responsive Verification

**Files:**
- Modify: `/home/huyquang/Desktop/website_truyen/index.html`

**Interfaces:**
- Consumes: `switchRepo()`, `toggleOnlyFavorites()`, `toggleMobileSidebar()`
- Produces: Polished mobile layout with bottom navigation bar and touch-friendly interactions.

- [ ] **Step 1: Add Mobile Bottom Navigation Bar**
  - Add fixed bottom bar with 4 quick links:
    - 🏠 Trang Chủ (`switchRepo('home')`)
    - 🎬 Kho Video (`switchRepo('manhua_review')`)
    - 📚 Truyện Tranh (`switchRepo('truyen_tranh')`)
    - ❤️ Tủ Sách (`toggleOnlyFavorites()`)
  - Ensure it stays visible only on mobile screens (`max-width: 900px`).

- [ ] **Step 2: Add bottom padding on mobile**
  - Ensure content is not obscured by the bottom navigation bar on mobile viewports.

- [ ] **Step 3: Run comprehensive verification**
  - Test desktop, tablet, and mobile viewport sizes.
  - Test searching, sorting, filtering, opening modals, adding/removing favorites.
  - Verify Firebase data sync still triggers badge and stat updates seamlessly.

- [ ] **Step 4: Commit & Deploy**
  ```bash
  git add index.html
  git commit -m "feat: complete Hyu Multiverse Homepage, mobile bottom nav and UI overhaul"
  git push origin main
  ```
