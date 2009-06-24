#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Statistical tracking and reports
=================================
"""
__docformat__ = 'restructuredtext'

# we track statistics over the life of the deck, and per-day
STATS_LIFE = 0
STATS_DAY = 1

import unicodedata, time, sys, os
import anki, anki.utils
from datetime import date
from anki.db import *
from anki.lang import _

# Tracking stats on the DB
##########################################################################

statsTable = Table(
    'stats', metadata,
    Column('id', Integer, primary_key=True),
    Column('type', Integer, nullable=False),
    # for LIFE, update to time of first review?
    Column('day', Date, nullable=False, default=date.today),
    Column('reps', Integer, nullable=False, default=0),
    Column('averageTime', Float, nullable=False, default=0),
    Column('reviewTime', Float, nullable=False, default=0),
    Column('distractedTime', Float, nullable=False, default=0),
    Column('distractedReps', Integer, nullable=False, default=0),
    Column('newEase0', Integer, nullable=False, default=0),
    Column('newEase1', Integer, nullable=False, default=0),
    Column('newEase2', Integer, nullable=False, default=0),
    Column('newEase3', Integer, nullable=False, default=0),
    Column('newEase4', Integer, nullable=False, default=0),
    Column('youngEase0', Integer, nullable=False, default=0),
    Column('youngEase1', Integer, nullable=False, default=0),
    Column('youngEase2', Integer, nullable=False, default=0),
    Column('youngEase3', Integer, nullable=False, default=0),
    Column('youngEase4', Integer, nullable=False, default=0),
    Column('matureEase0', Integer, nullable=False, default=0),
    Column('matureEase1', Integer, nullable=False, default=0),
    Column('matureEase2', Integer, nullable=False, default=0),
    Column('matureEase3', Integer, nullable=False, default=0),
    Column('matureEase4', Integer, nullable=False, default=0))

class Stats(object):
    def __init__(self, type):
        self.type = type
        if type == STATS_LIFE:
            self.id = 1

mapper(Stats, statsTable)

def updateAllStats(s, card, ease, oldState):
    "Update global and daily statistics."
    updateStats(globalStats(s), card, ease, oldState)
    updateStats(dailyStats(s), card, ease, oldState)

def updateStats(stats, card, ease, oldState):
    stats.reps += 1
    delay = card.thinkingTime()
    if delay >= 60:
        # make a guess as to the time spent answering
        stats.reviewTime += stats.averageTime
        stats.distractedTime += delay - 60
        stats.distractedReps += 1
    else:
        stats.reviewTime += delay
        stats.averageTime = (
            stats.reviewTime / float(stats.reps - stats.distractedReps))
    # update eases
    attr = oldState + "Ease%d" % ease
    setattr(stats, attr, getattr(stats, attr) + 1)

def globalStats(s):
    glob = s.query(Stats).get(1)
    if not glob:
        glob = Stats(STATS_LIFE)
        s.save(glob)
        s.flush()
    return glob

def dailyStats(s):
    today = s.query(Stats).filter_by(type=1).filter_by(day=date.today()).first()
    if not today:
        today = Stats(STATS_DAY)
        s.save(today)
        s.flush()
    return today

def summarizeStats(stats, pre=""):
    "Generate percentages and total counts for STATS. Optionally prefix."
    cardTypes = ("new", "young", "mature")
    h = {}
    # total counts
    ###############
    for type in cardTypes:
        # total yes/no for type, eg. gNewYes
        h[pre + type.capitalize() + "No"] = (getattr(stats, type + "Ease0") +
                                             getattr(stats, type + "Ease1"))
        h[pre + type.capitalize() + "Yes"] = (getattr(stats, type + "Ease2") +
                                              getattr(stats, type + "Ease3") +
                                              getattr(stats, type + "Ease4"))
        # total for type, eg. gNewTotal
        h[pre + type.capitalize() + "Total"] = (
            h[pre + type.capitalize() + "No"] +
            h[pre + type.capitalize() + "Yes"])
    # total yes/no, eg. gYesTotal
    for answer in ("yes", "no"):
        num = 0
        for type in cardTypes:
            num += h[pre + type.capitalize() + answer.capitalize()]
        h[pre + answer.capitalize() + "Total"] = num
    # total over all, eg. gTotal
    num = 0
    for type in cardTypes:
        num += h[pre + type.capitalize() + "Total"]
    h[pre + "Total"] = num
    # percentages
    ##############
    for type in cardTypes:
        # total yes/no % by type, eg. gNewYes%
        for answer in ("yes", "no"):
            setPercentage(h, pre + type.capitalize() + answer.capitalize(),
                          pre + type.capitalize())
    for answer in ("yes", "no"):
        # total yes/no, eg. gYesTotal%
        setPercentage(h, pre + answer.capitalize() + "Total", pre)
    h[pre + 'AverageTime'] = stats.averageTime
    h[pre + 'ReviewTime'] = stats.reviewTime
    h[pre + 'DistractedTime'] = stats.distractedTime
    return h

def setPercentage(h, a, b):
    try:
        h[a + "%"] = (h[a] / float(h[b + "Total"])) * 100
    except ZeroDivisionError:
        h[a + "%"] = 0

def getStats(s):
    "Return a handy dictionary exposing a number of internal stats."
    h = {}
    h.update(summarizeStats(globalStats(s), "g"))
    h.update(summarizeStats(dailyStats(s), "d"))

    return h

# Card stats
##########################################################################

class CardStats(object):

    def __init__(self, deck, card):
        self.deck = deck
        self.card = card

    def report(self):
        c = self.card
        self.txt = "<table width=250>"
        self.addLine(_("Added"), self.strTime(c.created))
        if c.firstAnswered:
            self.addLine(_("First review"), self.strTime(c.firstAnswered))
        self.addLine(_("Changed"), self.strTime(c.modified))
        next = time.time() - c.due
        if next > 0:
            next = _("%s ago") % anki.utils.fmtTimeSpan(next)
        else:
            next = _("in %s") % anki.utils.fmtTimeSpan(abs(next))
        self.addLine(_("Next due"), next)
        self.addLine(_("Current interval"), "%0.2f days" % c.interval)
        if c.interval != c.lastInterval:
            # don't show the last interval if it hasn't been updated yet
            self.addLine(_("Last interval"), "%0.2f days" % c.lastInterval)
        self.addLine(_("Current factor"), "%0.2f" % c.factor)
        self.addLine(_("Last factor"), "%0.2f" % c.lastFactor)
        self.addLine(_("Review count"), c.reps)
        if c.reps:
            self.addLine(_("Correct count"), "%d (%0.2f%%)" % (
                c.yesCount, (c.yesCount / float(c.reps))*100))
        self.addLine(_("Repeatedly correct"), c.successive)
        self.addLine(_("Average time"), _("%0.1f seconds") %
                     c.averageTime)
        self.addLine(_("Total time"), _("%0.1f seconds") %
                     c.reviewTime)
        if self.deck.cardIsNew(c):
            state = _("First time")
        elif self.deck.cardIsBeingLearnt(c):
            state = _("Young")
        else:
            state = _("Mature")
        self.addLine(_("State"), state)
        if c.tags:
            self.addLine(_("Card tags"), c.tags)
        self.addLine(_("Card model tags"), c.cardModel.name)
        if c.fact.model.tags:
            self.addLine(_("Model tags"), c.fact.model.tags)
        if c.fact.tags:
            self.addLine(_("Fact tags"), c.fact.tags)
        self.txt += "</table>"
        return self.txt

    def addLine(self, k, v):
        self.txt += "<tr><td><b>%s<b></td><td>%s</td></tr>" % (k, v)

    def strTime(self, tm):
        s = anki.utils.fmtTimeSpan(time.time() - tm)
        return _("%s ago") % s

# Deck stats (specific to the 'sched' scheduler)
##########################################################################

class DeckStats(object):

    def __init__(self, deck):
        self.deck = deck

    def report(self):
        "Return an HTML string with a report."
        if self.deck.isEmpty():
            return _("Please add some cards first.<p/>")
        d = self.deck
        html="<h1>" + _("Deck Statistics") + "</h1>"
        html += _("Deck created: <b>%s</b> ago<br>") % self.createdTimeStr()
        total = d.totalCardCount()
        new = d.newCardCount()
        young = d.youngCardCount()
        old = d.matureCardCount()
        newP = new / float(total) * 100
        youngP = young / float(total) * 100
        oldP = old / float(total) * 100
        stats = d.getStats()
        (stats["new"], stats["newP"]) = (new, newP)
        (stats["old"], stats["oldP"]) = (old, oldP)
        (stats["young"], stats["youngP"]) = (young, youngP)
        html += _("Total number of cards: <b>%d</b><br><br>") % total

        html += _("<b>Card counts</b><br>")
        html += _("Mature cards: <b>%(old)d</b> "
                  "(<b>%(oldP)0.2f%%</b>)<br>") % stats
        html += _("Young cards: <b>%(young)d</b> "
                  "(<b>%(youngP)0.2f%%</b>)<br>") % stats
        html += _("Unseen cards: <b>%(new)d</b> "
                  "(<b>%(newP)0.2f%%</b>)<br><br>") % stats

        html += _("<b>Correct answers</b><br>")
        html += _("Mature cards: <b>%(gMatureYes%)0.1f%%</b> "
                  "(<b>%(gMatureYes)d</b> of <b>%(gMatureTotal)d</b>)<br>") % stats
        html += _("Young cards: <b>%(gYoungYes%)0.1f%%</b> "
                  "(<b>%(gYoungYes)d</b> of <b>%(gYoungTotal)d</b>)<br>") % stats
        html += _("First-seen cards: <b>%(gNewYes%)0.1f%%</b> "
                  "(<b>%(gNewYes)d</b> of <b>%(gNewTotal)d</b>)<br><br>") % stats
        # average pending time
        existing = d.totalCardCount() - d.newCardCount()
        avgInt = self.getAverageInterval()
        if existing and avgInt:
            html += _("<b>Averages</b><br>")
            html += _("Interval: <b>%0.0f</b> days<br/>") % avgInt
            html += _("Workload: <b>%0.1f</b> cards/day<br/>") % (
                existing / float(avgInt))
            html += _("Added: <b>%(a)d</b> a day, <b>%(b)d</b> a month<br>") % {
                'a': self.newPerDay(), 'b': self.newPerDay()*30}
        return html

    def getAverageInterval(self):
        return self.deck.s.scalar(
            "select sum(interval) / count(interval) from cards "
            "where cards.reps > 0") or 0

    def intervalReport(self, intervals, labels, total):
        boxes = self.splitIntoIntervals(intervals)
        keys = boxes.keys()
        keys.sort()
        html = ""
        for key in keys:
            html += ("<tr><td align=right>%s</td><td align=right>" +
                     "%d</td><td align=right>%0.2f%%</td></tr>") % (
                labels[key],
                boxes[key],
                boxes[key] / float(total) * 100)
        return html

    def splitIntoIntervals(self, intervals):
        boxes = {}
        n = 0
        for i in range(len(intervals) - 1):
            (min, max) = (intervals[i], intervals[i+1])
            for c in self.deck:
                if c.interval > min and c.interval <=  max:
                    boxes[n] = boxes.get(n, 0) + 1
            n += 1
        return boxes

    def newPerDay(self):
        "Average number of new cards added each day."
        return self.deck.totalCardCount() / max(1, self.ageInDays())

    def createdTimeStr(self):
        return anki.utils.fmtTimeSpan(time.time() - self.deck.created)

    def ageInDays(self):
        return (time.time() - self.deck.created) / 86400.0


# Kanji stats
##########################################################################

def asHTMLDocument(text):
    "Return text wrapped in a HTML document."
    return ("""
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html>
    <head>
    <meta http-equiv=content-type content="text/html; charset=utf-8">
    </head>
    <body>
    %s
    </body>
    </html>
    """ % text.encode("utf-8"))

def isKanji(unichar):
    try:
        return unicodedata.name(unichar).find('CJK UNIFIED IDEOGRAPH') >= 0
    except ValueError:
        # a control character
        return False

class KanjiStats(object):

    def __init__(self, deck):
        self.deck = deck
        self._gradeHash = dict()
        for (name, chars), grade in zip(self.kanjiGrades,
                                        xrange(len(self.kanjiGrades))):
            for c in chars:
                self._gradeHash[c] = grade

    def kanjiGrade(self, unichar):
        return self._gradeHash.get(unichar, 0)

    # FIXME: as it's html, the width doesn't matter
    def kanjiCountStr(self, gradename, count, total=0, width=0):
        d = {'count': self.rjustfig(count, width), 'gradename': gradename}
        if total:
            d['total'] = self.rjustfig(total, width)
            d['percent'] = float(count)/total*100
            return _("%(gradename)s: %(count)s of %(total)s (%(percent)0.1f%%).") % d
        else:
            return _("%(count)s %(gradename)s kanji.") % d

    def rjustfig(self, n, width):
        n = unicode(n)
        return n + "&nbsp;" * (width - len(n))

    def genKanjiSets(self):
        self.kanjiSets = [set([]) for g in self.kanjiGrades]
        all = "".join(self.deck.s.column0("""
select value from cards, fields
where
cards.reps > 0 and
cards.factId = fields.factId
"""))
        for u in all:
            if isKanji(u):
                self.kanjiSets[self.kanjiGrade(u)].add(u)

    def report(self):
        self.genKanjiSets()
        counts = [(name, len(found), len(all)) \
                  for (name, all), found in zip(self.kanjiGrades, self.kanjiSets)]
        out = (_("<h1>Kanji statistics</h1>The %d seen cards in this deck "
                 "contain:") % self.deck.oldCardCount() +
               "<br/><ul>" +
               # total kanji
               _("<li>%d total unique kanji.</li>") %
               sum([c[1] for c in counts]) +
               # total joyo
               "<li>%s</li>" % self.kanjiCountStr(
            u'Jouyou',sum([c[1] for c in counts[1:8]]),
            sum([c[2] for c in counts[1:8]])) +
               # total jinmei
               "<li>%s</li>" % self.kanjiCountStr(*counts[8]) +
               # total non-joyo
               "<li>%s</li>" % self.kanjiCountStr(*counts[0]))

        out += "</ul><p/>" + _(u"Jouyou levels:") + "<p/><ul>"
        L = ["<li>" + self.kanjiCountStr(c[0],c[1],c[2], width=3) + "</li>"
             for c in counts[1:8]]
        out += "".join(L)
        out += "</ul>"
        return out

    def missingReport(self):
        out = "<h1>Missing kanji</h1>"
        for grade in range(1, 9):
            missing = "".join(self.missingInGrade(grade))
            if not missing:
                continue
            out += "<h2>" + self.kanjiGrades[grade][0] + "</h2>"
            out += "<font size=+4>"
            while 1:
                if not missing:
                    break
                # edict will take up to about 10 kanji at once
                out += self.edictKanjiLink(missing[0:10])
                missing = missing[10:]
            out += "</font>"
        return out + "<br/>"

    def edictKanjiLink(self, kanji):
        base="http://www.csse.monash.edu.au/~jwb/cgi-bin/wwwjdic.cgi?1MMJ"
        url=base + kanji
        return '<a href="%s">%s</a>' % (url, kanji)

    def missingInGrade(self, gradeNum):
        existingKanji = self.kanjiSets[gradeNum]
        totalKanji = self.kanjiGrades[gradeNum][1]
        return [k for k in totalKanji if k not in existingKanji]

    kanjiGrades = [
        (u'non-jouyou', ''),
        (u'Grade 1', u'一右雨円王音下火花貝学気休玉金九空月犬見五口校左三山四子糸字耳七車手十出女小上森人水正生青石赤先千川早草足村大男竹中虫町天田土二日入年白八百文本名木目夕立力林六'),
        (u'Grade 2', u'引羽雲園遠黄何夏家科歌画会回海絵外角楽活間丸岩顔帰汽記弓牛魚京強教近兄形計元原言古戸午後語交光公工広考行高合国黒今才細作算姉市思止紙寺時自室社弱首秋週春書少場色食心新親図数星晴声西切雪線船前組走多太体台谷知地池茶昼朝長鳥直通弟店点電冬刀東当答頭同道読内南肉馬買売麦半番父風分聞米歩母方北妹毎万明鳴毛門夜野矢友曜用来理里話'),
        (u'Grade 3', u'悪安暗委意医育員飲院運泳駅央横屋温化荷界開階寒感漢館岸期起客宮急球究級去橋業局曲銀区苦具君係軽決血研県庫湖向幸港号根祭坂皿仕使始指死詩歯事持次式実写者主取守酒受州拾終習集住重宿所暑助勝商昭消章乗植深申真神身進世整昔全想相送息速族他打対待代第題炭短談着柱注丁帳調追定庭笛鉄転登都度島投湯等豆動童農波配倍箱畑発反板悲皮美鼻筆氷表病秒品負部服福物平返勉放味命面問役薬油有由遊予様洋羊葉陽落流旅両緑礼列練路和'),
        (u'Grade 4', u'愛案以位囲胃衣印栄英塩億加果課貨芽改械害街各覚完官管観関願喜器希旗機季紀議救求泣給挙漁競共協鏡極訓軍郡型径景芸欠結健建験固候功好康航告差最菜材昨刷察札殺参散産残司史士氏試児治辞失借種周祝順初唱松焼照省笑象賞信臣成清静席積折節説戦浅選然倉巣争側束続卒孫帯隊達単置仲貯兆腸低停底的典伝徒努灯働堂得特毒熱念敗梅博飯費飛必標票不付夫府副粉兵別変辺便包法望牧末満未脈民無約勇要養浴利陸料良量輪類令例冷歴連労老録'),
        (u'Grade 5', u'圧易移因営永衛液益演往応恩仮価可河過賀解快格確額刊幹慣眼基寄規技義逆久旧居許境興均禁句群経潔件券検険減現限個故護効厚構耕講鉱混査再妻採災際在罪財桜雑賛酸師志支枝資飼似示識質舎謝授修術述準序承招証常情条状織職制勢性政精製税績責接設絶舌銭祖素総像増造則測属損態貸退団断築張提程敵適統導銅徳独任燃能破判版犯比肥非備俵評貧婦富布武復複仏編弁保墓報豊暴貿防務夢迷綿輸余預容率略留領'),
        (u'Grade 6', u'異遺域宇映延沿我灰拡閣革割株巻干看簡危揮机貴疑吸供胸郷勤筋敬系警劇激穴憲権絹厳源呼己誤后孝皇紅鋼降刻穀骨困砂座済裁策冊蚕姿私至視詞誌磁射捨尺若樹収宗就衆従縦縮熟純処署諸除傷将障城蒸針仁垂推寸盛聖誠宣専泉洗染善創奏層操窓装臓蔵存尊宅担探誕暖段値宙忠著庁潮頂賃痛展党糖討届難乳認納脳派俳拝背肺班晩否批秘腹奮並閉陛片補暮宝訪亡忘棒枚幕密盟模訳優郵幼欲翌乱卵覧裏律臨朗論'),
        (u'JuniorHS', u'亜哀握扱依偉威尉慰為維緯違井壱逸稲芋姻陰隠韻渦浦影詠鋭疫悦謁越閲宴援炎煙猿縁鉛汚凹奥押欧殴翁沖憶乙卸穏佳嫁寡暇架禍稼箇華菓蚊雅餓介塊壊怪悔懐戒拐皆劾慨概涯該垣嚇核殻獲穫較郭隔岳掛潟喝括渇滑褐轄且刈乾冠勘勧喚堪寛患憾換敢棺款歓汗環甘監緩缶肝艦貫還鑑閑陥含頑企奇岐幾忌既棋棄祈軌輝飢騎鬼偽儀宜戯擬欺犠菊吉喫詰却脚虐丘及朽窮糾巨拒拠虚距享凶叫峡恐恭挟況狂狭矯脅響驚仰凝暁斤琴緊菌襟謹吟駆愚虞偶遇隅屈掘靴繰桑勲薫傾刑啓契恵慶憩掲携渓継茎蛍鶏迎鯨撃傑倹兼剣圏堅嫌懸献肩謙賢軒遣顕幻弦玄孤弧枯誇雇顧鼓互呉娯御悟碁侯坑孔巧恒慌抗拘控攻更江洪溝甲硬稿絞綱肯荒衡貢購郊酵項香剛拷豪克酷獄腰込墾婚恨懇昆紺魂佐唆詐鎖債催宰彩栽歳砕斎載剤咲崎削搾索錯撮擦傘惨桟暫伺刺嗣施旨祉紫肢脂諮賜雌侍慈滋璽軸執湿漆疾芝赦斜煮遮蛇邪勺爵酌釈寂朱殊狩珠趣儒寿需囚愁秀臭舟襲酬醜充柔汁渋獣銃叔淑粛塾俊瞬准循旬殉潤盾巡遵庶緒叙徐償匠升召奨宵尚床彰抄掌昇晶沼渉焦症硝礁祥称粧紹肖衝訟詔詳鐘丈冗剰壌嬢浄畳譲醸錠嘱飾殖触辱伸侵唇娠寝審慎振浸紳薪診辛震刃尋甚尽迅陣酢吹帥炊睡粋衰遂酔錘随髄崇枢据杉澄瀬畝是姓征牲誓請逝斉隻惜斥析籍跡拙摂窃仙占扇栓潜旋繊薦践遷銑鮮漸禅繕塑措疎礎租粗訴阻僧双喪壮捜掃挿曹槽燥荘葬藻遭霜騒憎贈促即俗賊堕妥惰駄耐怠替泰滞胎袋逮滝卓択拓沢濯託濁諾但奪脱棚丹嘆淡端胆鍛壇弾恥痴稚致遅畜蓄逐秩窒嫡抽衷鋳駐弔彫徴懲挑眺聴脹超跳勅朕沈珍鎮陳津墜塚漬坪釣亭偵貞呈堤帝廷抵締艇訂逓邸泥摘滴哲徹撤迭添殿吐塗斗渡途奴怒倒凍唐塔悼搭桃棟盗痘筒到謄踏逃透陶騰闘洞胴峠匿督篤凸突屯豚曇鈍縄軟尼弐如尿妊忍寧猫粘悩濃把覇婆廃排杯輩培媒賠陪伯拍泊舶薄迫漠爆縛肌鉢髪伐罰抜閥伴帆搬畔繁般藩販範煩頒盤蛮卑妃彼扉披泌疲碑罷被避尾微匹姫漂描苗浜賓頻敏瓶怖扶敷普浮符腐膚譜賦赴附侮舞封伏幅覆払沸噴墳憤紛雰丙併塀幣弊柄壁癖偏遍舗捕穂募慕簿倣俸奉峰崩抱泡砲縫胞芳褒邦飽乏傍剖坊妨帽忙房某冒紡肪膨謀僕墨撲朴没堀奔翻凡盆摩磨魔麻埋膜又抹繭慢漫魅岬妙眠矛霧婿娘銘滅免茂妄猛盲網耗黙戻紋匁厄躍柳愉癒諭唯幽悠憂猶裕誘雄融与誉庸揚揺擁溶窯謡踊抑翼羅裸頼雷絡酪欄濫吏履痢離硫粒隆竜慮虜了僚寮涼猟療糧陵倫厘隣塁涙累励鈴隷零霊麗齢暦劣烈裂廉恋錬炉露廊楼浪漏郎賄惑枠湾腕'),
        (u'Jinmeiyou', u'阿葵茜渥旭梓絢綾鮎杏伊惟亥郁磯允胤卯丑唄叡瑛艶苑於旺伽嘉茄霞魁凱馨叶樺鎌茅侃莞巌伎嬉毅稀亀誼鞠橘亨匡喬尭桐錦欣欽芹衿玖矩駒熊栗袈圭慧桂拳絃胡虎伍吾梧瑚鯉倖宏弘昂晃浩紘鴻嵯沙瑳裟哉采冴朔笹皐燦獅爾蒔汐鹿偲紗洲峻竣舜駿淳醇曙渚恕庄捷昌梢菖蕉丞穣晋榛秦須翠瑞嵩雛碩曽爽惣綜聡蒼汰黛鯛鷹啄琢只辰巽旦檀智猪暢蝶椎槻蔦椿紬鶴悌汀禎杜藤憧瞳寅酉惇敦奈那凪捺楠虹乃之巴萩肇鳩隼斐緋眉柊彦媛彪彬芙楓蕗碧甫輔朋萌鳳鵬睦槙柾亦麿巳稔椋孟也冶耶弥靖佑宥柚湧祐邑楊耀蓉遥嵐藍蘭李梨璃琉亮凌瞭稜諒遼琳麟瑠伶嶺怜玲蓮呂禄倭亘侑勁奎崚彗昴晏晨晟暉栞椰毬洸洵滉漱澪燎燿瑶皓眸笙綺綸翔脩茉莉菫詢諄赳迪頌颯黎凜熙')
        ]
