<#
Render a crisp 1280x640 social-preview PNG (og:image) for Clearframe (agy-readglass)
using Windows System.Drawing with anti-aliased typography.
#>

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$outPath = Join-Path $PSScriptRoot "..\docs\assets\social-preview.png"
$outDir = Split-Path $outPath -Parent
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$W = 1280
$H = 640
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

function New-RoundedRectPath([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function Color-Hex([string]$hex, [int]$alpha = 255) {
    $c = [System.Drawing.ColorTranslator]::FromHtml($hex)
    return [System.Drawing.Color]::FromArgb($alpha, $c.R, $c.G, $c.B)
}

# Background canvas + subtle amber & mint glows
$g.Clear((Color-Hex "#0b0d11"))
$amberGlow = New-Object System.Drawing.Drawing2D.GraphicsPath
$amberGlow.AddEllipse(-120, -140, 620, 620)
$amberBrush = New-Object System.Drawing.Drawing2D.PathGradientBrush($amberGlow)
$amberBrush.CenterColor = Color-Hex "#e0a45a" 36
$amberBrush.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 224, 164, 90))
$g.FillPath($amberBrush, $amberGlow)

$mintGlow = New-Object System.Drawing.Drawing2D.GraphicsPath
$mintGlow.AddEllipse(800, 240, 620, 560)
$mintBrush = New-Object System.Drawing.Drawing2D.PathGradientBrush($mintGlow)
$mintBrush.CenterColor = Color-Hex "#3ecf8e" 30
$mintBrush.SurroundColors = @([System.Drawing.Color]::FromArgb(0, 62, 207, 142))
$g.FillPath($mintBrush, $mintGlow)

# Outer subtle frame
$framePath = New-RoundedRectPath 28 28 ($W - 56) ($H - 56) 22
$framePen = New-Object System.Drawing.Pen((Color-Hex "#ebe7df" 32), 1.5)
$g.DrawPath($framePen, $framePath)

# Left branding column
$fBadge = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fTitle = New-Object System.Drawing.Font("Segoe UI", 46, [System.Drawing.FontStyle]::Bold)
$fSub   = New-Object System.Drawing.Font("Segoe UI", 19, [System.Drawing.FontStyle]::Regular)
$fBody  = New-Object System.Drawing.Font("Segoe UI", 15, [System.Drawing.FontStyle]::Regular)
$fMono  = New-Object System.Drawing.Font("Consolas", 14, [System.Drawing.FontStyle]::Bold)
$fCardT = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fCardS = New-Object System.Drawing.Font("Consolas", 12, [System.Drawing.FontStyle]::Regular)

# Top pill badge
$pillPath = New-RoundedRectPath 76 74 440 38 19
$g.FillPath((New-Object System.Drawing.SolidBrush((Color-Hex "#e0a45a" 34))), $pillPath)
$g.DrawPath((New-Object System.Drawing.Pen((Color-Hex "#e0a45a" 110), 1.2)), $pillPath)
$g.DrawString("ANTIGRAVITY  •  WCAG AA/AAA + APCA", $fBadge, (New-Object System.Drawing.SolidBrush((Color-Hex "#e0a45a"))), 96, 81)

# Title & tagline
$g.DrawString("Clearframe", $fTitle, (New-Object System.Drawing.SolidBrush((Color-Hex "#ebe7df"))), 72, 138)
$g.DrawString("agy-readglass", (New-Object System.Drawing.Font("Consolas", 26, [System.Drawing.FontStyle]::Bold)), (New-Object System.Drawing.SolidBrush((Color-Hex "#8aa4b8"))), 76, 212)

$g.DrawString("Work-session glass themes for Antigravity", $fSub, (New-Object System.Drawing.SolidBrush((Color-Hex "#ebe7df"))), 76, 274)
$g.DrawString("that stay readable for 8-hour sessions.", $fSub, (New-Object System.Drawing.SolidBrush((Color-Hex "#b7c0cc"))), 76, 308)

# Feature chips
$chips = @(
    @("6 Work-Session Presets", "#e0a45a"),
    @("OKLCH Theme Scaffolder", "#3ecf8e"),
    @("Rescue Existing themes.json", "#8aa4b8"),
    @("3 Standalone Agent Skills", "#d4a574")
)
$cy = 376
foreach ($ch in $chips) {
    $chipPath = New-RoundedRectPath 76 $cy 340 40 10
    $g.FillPath((New-Object System.Drawing.SolidBrush((Color-Hex "#141820" 230))), $chipPath)
    $g.DrawPath((New-Object System.Drawing.Pen((Color-Hex $ch[1] 90), 1.2)), $chipPath)
    $g.FillEllipse((New-Object System.Drawing.SolidBrush((Color-Hex $ch[1]))), 94, $cy + 14, 12, 12)
    $g.DrawString($ch[0], $fBody, (New-Object System.Drawing.SolidBrush((Color-Hex "#ebe7df"))), 118, $cy + 8)
    $cy += 50
}

# Right showcase: 2x3 preset swatch cards
$cards = @(
    @("Deep Ink", "AI 15.5:1 | Lc -92", "#0c0e12", "#e0a45a", "#ebe7df", "#b7c0cc"),
    @("Review Split", "AI 15.0:1 | Lc -92", "#0d141c", "#d4a574", "#ebe7df", "#c5ced6"),
    @("Lantern Hour", "AI 15.2:1 | Lc -92", "#1a100c", "#e8a15a", "#efe6d8", "#d2c4b4"),
    @("Mekong Morning", "AI 17.0:1 | Lc +102", "#f4f1ea", "#1f6b45", "#1c1915", "#5c564c"),
    @("Screenshot Clean", "AI 15.3:1 | Lc -93", "#121316", "#9aa3b2", "#e9e9e7", "#b8b8be"),
    @("Delta Mint", "AI 15.9:1 | Lc -94", "#0c1210", "#3ecf8e", "#e5ede9", "#b2c1ba")
)

$startX = 635
$startY = 74
$cw = 276
$chh = 144
$gapX = 20
$gapY = 18

for ($i = 0; $i -lt $cards.Count; $i++) {
    $c = $cards[$i]
    $col = $i % 2
    $row = [Math]::Floor($i / 2)
    $x = $startX + $col * ($cw + $gapX)
    $y = $startY + $row * ($chh + $gapY)

    $cp = New-RoundedRectPath $x $y $cw $chh 14
    $g.FillPath((New-Object System.Drawing.SolidBrush((Color-Hex $c[2]))), $cp)
    $g.DrawPath((New-Object System.Drawing.Pen((Color-Hex $c[3] 150), 1.6)), $cp)

    $g.FillEllipse((New-Object System.Drawing.SolidBrush((Color-Hex $c[3]))), $x + 18, $y + 18, 14, 14)
    $g.DrawString($c[0], $fCardT, (New-Object System.Drawing.SolidBrush((Color-Hex $c[4]))), $x + 42, $y + 14)
    $g.DrawString("Clearframe Preset • AAA", (New-Object System.Drawing.Font("Segoe UI", 11)), (New-Object System.Drawing.SolidBrush((Color-Hex $c[5]))), $x + 18, $y + 50)

    $badgeP = New-RoundedRectPath ($x + 18) ($y + 88) 240 34 8
    $g.FillPath((New-Object System.Drawing.SolidBrush((Color-Hex $c[3] 34))), $badgeP)
    $g.DrawPath((New-Object System.Drawing.Pen((Color-Hex $c[3] 100), 1)), $badgeP)
    $g.DrawString($c[1], $fCardS, (New-Object System.Drawing.SolidBrush((Color-Hex $c[4]))), $x + 28, $y + 95)
}

$fFooter = New-Object System.Drawing.Font("Consolas", 12, [System.Drawing.FontStyle]::Bold)
$g.DrawString("github.com/vuloc080611/agy-readglass  •  MIT License", $fFooter, (New-Object System.Drawing.SolidBrush((Color-Hex "#8aa4b8"))), 635, 566)

$bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose()
$bmp.Dispose()
Write-Output "Saved $outPath ($W x $H)"
