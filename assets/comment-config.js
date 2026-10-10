// 作品评论功能配置。
//
// 评论内容保存在腾讯云开发（Twikoo 留言系统）。开通并部署之后，
// 把下面 envId 换成你自己的环境 ID（形如 env-xxxxxxxxxxxxxxxx）即可启用；
// envId 保持为空时，整个网站不会加载任何评论相关的文件，行为与未接入时完全一致。
//
// 开通步骤见 docs/评论功能开通指南.md。
window.STUDIO_COMMENT_CONFIG = {
  envId: '', // ← 填入你的腾讯云开发环境 ID 后启用
  region: 'ap-shanghai', // 环境地域，若不在上海请改成对应地域
  funcName: 'twikoo', // 云函数名称，与云端保持一致
  version: '2.0.13', // 前端版本，需与云函数版本一致
};