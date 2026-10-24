# 挂梯子机场图标归档

图标来源：<https://guatizi.com/>

图片由 GitHub Actions 从站点公开页面自动抓取，存放在 `icons/guatizi/`，并生成 `manifest.json` 记录原始页面、原图地址和抓取状态。

## 首次同步

1. 打开仓库的 **Actions** 页面。
2. 选择 **Sync Guatizi Airport Icons**。
3. 点击 **Run workflow**，再次点击确认。
4. 运行结束后查看 `icons/guatizi/`。

工作流每周一也会自动运行。部分页面可能没有可识别的机场 Logo，或只提供价格截图；这些项目会在 manifest 中标记为未找到，不会伪装成已下载。公开仓库再发布图片前，请留意原站及各图片权利人的授权要求。
