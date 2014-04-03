<?xml version="1.0" encoding="ASCII"?>
<!--This file was created automatically by html2xhtml-->
<!--from the HTML stylesheets.-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:doc="http://nwalsh.com/xsl/documentation/1.0" xmlns:stbl="http://nwalsh.com/xslt/ext/com.nwalsh.saxon.Table" xmlns:xtbl="xalan://com.nwalsh.xalan.Table" xmlns:lxslt="http://xml.apache.org/xslt" xmlns:ptbl="http://nwalsh.com/xslt/ext/xsltproc/python/Table" xmlns="http://www.w3.org/1999/xhtml" exclude-result-prefixes="doc stbl xtbl lxslt ptbl" version="1.0">

<xsl:include href="../common/table.xsl"/>

<!-- ********************************************************************
     $Id: table.xsl 8421 2009-05-04 07:49:49Z bobstayton $
     ********************************************************************

     This file is part of the XSL DocBook Stylesheet distribution.
     See ../README or http://docbook.sf.net/release/xsl/current/ for
     copyright and other information.

     ******************************************************************** -->

<lxslt:component prefix="xtbl" functions="adjustColumnWidths"/>

<xsl:template name="empty.table.cell">
  <xsl:param name="colnum" select="0"/>

  <xsl:variable name="rowsep">
    <xsl:choose>
      <!-- If this is the last row, rowsep never applies. -->
      <xsl:when test="not(ancestor-or-self::row[1]/following-sibling::row                           or ancestor-or-self::thead/following-sibling::tbody                           or ancestor-or-self::tbody/preceding-sibling::tfoot)">
        <xsl:value-of select="0"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inherited.table.attribute">
          <xsl:with-param name="entry" select="NOT-AN-ELEMENT-NAME"/>
          <xsl:with-param name="row" select="ancestor-or-self::row[1]"/>
          <xsl:with-param name="colnum" select="$colnum"/>
          <xsl:with-param name="attribute" select="'rowsep'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="colsep">
    <xsl:choose>
      <!-- If this is the last column, colsep never applies. -->
      <xsl:when test="number($colnum) &gt;= ancestor::tgroup/@cols">0</xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="inherited.table.attribute">
          <xsl:with-param name="entry" select="NOT-AN-ELEMENT-NAME"/>
          <xsl:with-param name="row" select="ancestor-or-self::row[1]"/>
          <xsl:with-param name="colnum" select="$colnum"/>
          <xsl:with-param name="attribute" select="'colsep'"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <td class="auto-generated">
    <xsl:if test="$table.borders.with.css != 0">
      <xsl:attribute name="style">
        <xsl:if test="$colsep &gt; 0">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'right'"/>
          </xsl:call-template>
        </xsl:if>
        <xsl:if test="$rowsep &gt; 0">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'bottom'"/>
          </xsl:call-template>
        </xsl:if>
      </xsl:attribute>
    </xsl:if>
    <xsl:text>&#160;</xsl:text>
  </td>
</xsl:template>

<!-- ==================================================================== -->

<xsl:template name="border">
  <xsl:param name="side" select="'left'"/>
  <xsl:param name="padding" select="0"/>
  <xsl:param name="style" select="$table.cell.border.style"/>
  <xsl:param name="color" select="$table.cell.border.color"/>
  <xsl:param name="thickness" select="$table.cell.border.thickness"/>

  <!-- Note: Some browsers (mozilla) require at least a width and style. -->

  <xsl:choose>
    <xsl:when test="($thickness != ''                      and $style != ''                      and $color != '')                     or ($thickness != ''                         and $style != '')                     or ($thickness != '')">
      <!-- use the compound property if we can: -->
      <!-- it saves space and probably works more reliab