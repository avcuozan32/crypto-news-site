<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9">
<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
  <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
      <title>XML Sitemap</title>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
      <style type="text/css">
        body { font-family: Arial, sans-serif; font-size: 12px; color: #333; }
        table { border: none; border-collapse: collapse; width: 100%; }
        th { text-align: left; padding: 5px; background-color: #f0f0f0; }
        td { padding: 5px; border-bottom: 1px solid #ddd; }
        .loc { word-wrap: break-word; }
      </style>
    </head>
    <body>
      <h1>Sitemap</h1>
      <table>
        <tr>
          <th>URL</th>
          <th>Last Modified</th>
        </tr>
        <xsl:for-each select="sitemap:sitemapindex/sitemap">
          <tr>
            <td class="loc">
              <xsl:value-of select="sitemap:loc"/>
            </td>
            <td>
              <xsl:value-of select="sitemap:lastmod"/>
            </td>
          </tr>
        </xsl:for-each>
      </table>
    </body>
  </html>
</xsl:template>
</xsl:stylesheet>