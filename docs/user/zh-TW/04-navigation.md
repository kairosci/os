# 導覽

Arch 裡的一切都靠鍵盤完成——_每件事都是！_ 系統剛啟動時，你光靠滑鼠真的什麼事都做不了。但你可以按下 `Super + Space` 叫出 Arch 選單，從這裡你幾乎什麼都能做。

但 Arch 選單甚至不是打算讓你在大多數時候用來操作系統的主要方式。我們可以比那更快！所有最重要的應用程式都直接綁定到各自的快捷鍵上。你用 `Super + Return` 啟動終端機，用 `Super + Shift + Return` 啟動瀏覽器。試著一個接著一個按，你就會看到 Hyprland 平鋪的魔法發揮作用：

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

接著你可以按下 `Super + J`，讓它們上下堆疊，而不是並排：

 ![navigation-stacked](images/navigation-stacked.webp)

再按一次 `Super + J`，它們就會回到並排的位置。然後在瀏覽器上試試 `Super + Shift + Arrow Right`，來交換這兩個視窗。

現在試試 `Super + Ctrl + T` 來啟動 Activity 監視器。它會以浮動視窗的形式出現。你可以用 `Super + T` 把它平鋪（再按一次就能讓它重新浮動）。現在按下 `Super + Shift + F` 開啟檔案管理器。你會得到一個整齊的四格配置：

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

你用 `Super + Arrow` 在你想啟用的視窗之間導覽。這會切換焦點，並把游標移到新應用程式的中心。

如果你按下 `Super + Shift + 2`，你會把目前焦點所在的應用程式移到第二個工作區。`Super + Shift + 1` 則把它移回來。（而 `Super + Shift + Alt + 2` 會把目前焦點所在的應用程式移到第二個工作區，但不切換過去）。

如果你按住 `Super` 並用滑鼠點一下視窗，你就能重新安排它的位置。如果你按住 `Super` 並使用滑鼠右鍵，你就能自由調整視窗大小。

你用 `Super + W` 或 `Super + Q` 關閉視窗（用 `Ctrl + Alt + Delete` 關閉所有視窗）。

你也可以用 `Super + F` 進入全螢幕，甚至只用 `Super + Alt + F` 進入全寬模式（保留頂部列），或用 `Super + Ctrl + F` 在視窗內全螢幕（看 YouTube 時很好用！）。

### Dwindle 與捲動式佈局

Arch 的預設佈局叫做 dwindle。它讓你在單一工作區開啟的所有視窗隨時都保持可見，即使必須為此把它們縮小也一樣。

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

但你也可以選擇把一個工作區改成捲動式佈局，在這種佈局下，視窗會並排排列，一路排到顯示器可見邊緣之外。你可以透過 `Super + L` 把單一工作區改成這種佈局。

再按一次 `Super + L` 會把工作區改成浮動式，在那裡視窗可以自由重疊，由你自行擺放，按第三次則回到 dwindle。`Super + Alt + L` 則依相反方向切換這些佈局。一個本來就在浮動的視窗——你用 `Super + T` 彈出來的那種，或總是以浮動方式開啟的應用程式——當工作區回到平鋪時，仍會保持浮動。頂部列會用你所在工作區的佈局來標示它：正方形代表 dwindle，圓形代表捲動式，三角形代表浮動式。點一下那個標記也會循環切換佈局。

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

這個選擇是以工作區為單位的，而且會保存下來。所以你可以讓工作區 1 保持 dwindle 用來瀏覽，工作區 2 保持捲動式用來寫程式，重新啟動後它們還會以同樣的樣子回來。

如果你希望把捲動式佈局設為預設，你可以在 `~/.config/hypr/looknfeel.lua` 裡這樣設定：

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### 將視窗分組

你可以使用 `Super + G` 將視窗分組。一旦你進入一個分組，你在那個狀態啟用時所啟動的每個視窗，都會屬於那個分組。你可以使用 `Super + Ctrl + Arrow Left/Right` 在這些已分組的視窗之間移動，或用 `Super + Alt + 1/2/3/4` 直接依順序前往已分組的視窗。

你可以用 `Super + Alt + G` 把一個視窗移出分組，或再按一次 `Super + G` 把整個分組拆散。最後，你可以用 `Super + Alt + Arrows` 把分組之外的視窗移進來。

### Scratchpad 工作區

最後，還有一個特殊的 scratchpad 工作區，它會像 Quake 主控台那樣，從你目前所在的工作區上方降下來。用 `Super + Grave` 或 `Super + S` 切換它，並用 `Super + Shift + Grave` 或 `Super + Alt + S` 在那裡放置一個視窗。

它特別適合用來放一個執行 agent 的終端機，或是你想快速互動但又不想離開目前工作區的控制項。要把視窗移出 scratchpad，直接用像是 `Super + Shift + 1` 之類的快捷鍵，把它送到另一個工作區即可。

當 scratchpad 只放著單一視窗時，它會以置中的面板形式落下，而不是橫跨整個螢幕。在上面放第二個應用程式，它就會回到全寬，這樣兩者就有空間並排坐好。

### 需要一點時間習慣！

要習慣像這樣導覽你的桌面需要一點時間，但一旦習慣了，你會很難再回去用傳統的滑鼠驅動桌面體驗！
