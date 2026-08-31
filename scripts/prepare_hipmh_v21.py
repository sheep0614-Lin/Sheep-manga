#!/usr/bin/env python3
from pathlib import Path
import shutil
import re

root = Path("upstream")
src = root / "src/zh/happymh"
dst = root / "src/zh/hipmh"

if not src.exists():
    raise SystemExit("找不到 upstream Happymh module")

if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)

for p in dst.rglob("*"):
    if not p.is_file():
        continue
    if p.suffix not in {".kt", ".java", ".xml", ".gradle", ".kts"}:
        continue
    text = p.read_text(encoding="utf-8")
    text = text.replace(
        "eu.kanade.tachiyomi.extension.zh.happymh",
        "eu.kanade.tachiyomi.extension.zh.hipmh",
    )
    text = text.replace("class Happymh", "class Hipmh")
    text = text.replace(".Happymh", ".Hipmh")
    text = text.replace("Happymh", "Hipmh")
    text = text.replace("嗨皮漫画", "嘻皮漫畫")
    text = text.replace("https://m.happymh.com", "https://m.hipmh.com")
    p.write_text(text, encoding="utf-8")

oldpkg = dst / "src/eu/kanade/tachiyomi/extension/zh/happymh"
newpkg = dst / "src/eu/kanade/tachiyomi/extension/zh/hipmh"
newpkg.mkdir(parents=True, exist_ok=True)

if oldpkg.exists():
    for f in list(oldpkg.iterdir()):
        shutil.move(str(f), str(newpkg / f.name))
    try:
        oldpkg.rmdir()
    except OSError:
        pass

oldmain = newpkg / "Happymh.kt"
if oldmain.exists():
    oldmain.unlink()

bg = dst / "build.gradle"
if bg.exists():
    t = bg.read_text(encoding="utf-8")
    t = re.sub(r"extName\s*=\s*'[^']+'", "extName = 'Hipmh'", t)
    t = re.sub(r"extClass\s*=\s*'[^']+'", "extClass = '.Hipmh'", t)
    t = re.sub(r"extVersionCode\s*=\s*\d+", "extVersionCode = 21", t)
    bg.write_text(t, encoding="utf-8")

hipmh_kt = r'''package eu.kanade.tachiyomi.extension.zh.hipmh

import eu.kanade.tachiyomi.network.GET
import eu.kanade.tachiyomi.source.model.FilterList
import eu.kanade.tachiyomi.source.model.MangasPage
import eu.kanade.tachiyomi.source.model.Page
import eu.kanade.tachiyomi.source.model.SChapter
import eu.kanade.tachiyomi.source.model.SManga
import eu.kanade.tachiyomi.source.online.HttpSource
import eu.kanade.tachiyomi.util.asJsoup
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.Headers
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import org.jsoup.nodes.Element
import java.util.Base64

class Hipmh : HttpSource() {

    override val name = "嘻皮漫畫"
    override val baseUrl = "https://m.hipmh.com"
    override val lang = "zh"
    override val supportsLatest = true

    private val apiBase = "https://hipapi1.s3file.top"

    override val client: OkHttpClient = network.cloudflareClient

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }

    override fun headersBuilder(): Headers.Builder =
        super.headersBuilder()
            .set("Referer", "$baseUrl/")
            .set(
                "User-Agent",
                "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 " +
                    "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36",
            )

    override fun popularMangaRequest(page: Int): Request =
        GET("$baseUrl/popularity", headers)

    override fun popularMangaParse(response: Response): MangasPage =
        MangasPage(parseWorkCards(response.asJsoup()), false)

    override fun latestUpdatesRequest(page: Int): Request =
        GET(baseUrl, headers)

    override fun latestUpdatesParse(response: Response): MangasPage {
        val document = response.asJsoup()
        val heading = document.select("h1, h2, h3, h4")
            .firstOrNull { it.text().contains("最新上架") }

        val scope = heading?.parent() ?: document
        var mangas = parseWorkCards(scope)
        if (mangas.isEmpty()) mangas = parseWorkCards(document)

        return MangasPage(mangas, false)
    }

    override fun searchMangaRequest(page: Int, query: String, filters: FilterList): Request {
        if (query.isBlank()) return GET("$baseUrl/explore", headers)

        val url = "$baseUrl/search".toHttpUrl().newBuilder()
            .addQueryParameter("q", query)
            .build()

        return GET(url, headers)
    }

    override fun searchMangaParse(response: Response): MangasPage =
        MangasPage(parseWorkCards(response.asJsoup()), false)

    override fun getFilterList() = FilterList()

    private fun parseWorkCards(root: Element): List<SManga> {
        val out = linkedMapOf<String, SManga>()

        root.select("a[href*=/works/]").forEach { a ->
            val href = a.attr("href").substringBefore("#")
            if (!href.contains("/works/")) return@forEach

            val abs = if (href.startsWith("http")) {
                href
            } else {
                "$baseUrl${if (href.startsWith("/")) "" else "/"}$href"
            }

            val path = abs.toHttpUrl().encodedPath
            val img = a.selectFirst("img")
                ?: a.parent()?.selectFirst("img")
                ?: return@forEach

            val title = img.attr("alt").trim().ifBlank {
                a.attr("title").trim().ifBlank {
                    a.select("h1, h2, h3, h4, h5, strong, span, p")
                        .map { it.text().trim() }
                        .firstOrNull { it.isNotBlank() }
                        .orEmpty()
                }
            }

            if (title.isBlank()) return@forEach

            val thumb = sequenceOf(
                img.attr("abs:src"),
                img.attr("abs:data-src"),
                img.attr("src"),
                img.attr("data-src"),
            ).firstOrNull { it.isNotBlank() }.orEmpty()

            out[path] = SManga.create().apply {
                this.title = title
                this.url = path
                thumbnail_url = thumb
            }
        }

        return out.values.toList()
    }

    override fun mangaDetailsParse(response: Response): SManga {
        val document = response.asJsoup()
        val aside = document.selectFirst("aside")

        val title = (
            aside?.selectFirst("h1")?.text()
                ?: document.selectFirst("h1")?.text()
                ?: document.title().substringBefore(" - 嬉皮漫畫")
            ).trim()

        val cover = sequenceOf(
            aside?.selectFirst("img")?.attr("abs:src"),
            document.selectFirst("meta[property=og:image]")?.attr("content"),
        ).firstOrNull { !it.isNullOrBlank() }

        val descriptionHeading = document.select("h2, h3, h4")
            .firstOrNull { it.text().contains("作品介紹") }

        val description = descriptionHeading
            ?.nextElementSibling()
            ?.text()
            ?.trim()
            .orEmpty()
            .ifBlank {
                document.selectFirst("meta[name=description]")?.attr("content").orEmpty()
            }

        val text = aside?.text().orEmpty()

        val author = aside?.select("a")
            ?.map { it.text().trim() }
            ?.firstOrNull { it.isNotBlank() && !it.startsWith("#") }

        val genres = aside?.select("a")
            ?.map { it.text().trim().removePrefix("#") }
            ?.filter {
                it.isNotBlank() &&
                    it != author &&
                    !it.contains("連載") &&
                    !it.contains("完結")
            }
            ?.distinct()
            ?.take(8)
            ?.joinToString(", ")

        val status = when {
            text.contains("完結") || text.contains("已完结") -> SManga.COMPLETED
            text.contains("連載") || text.contains("连载") -> SManga.ONGOING
            else -> SManga.UNKNOWN
        }

        return SManga.create().apply {
            this.title = title
            thumbnail_url = cover
            this.author = author
            artist = author
            genre = genres
            this.description = description
            this.status = status
        }
    }

    override fun chapterListRequest(manga: SManga): Request =
        GET("$baseUrl${manga.url}", headers)

    override fun chapterListParse(response: Response): List<SChapter> {
        val document = response.asJsoup()

        val config = document.selectFirst("#chapters-config")
        val midFromDom = config?.attr("data-mid").orEmpty()

        val workUrl = response.request.url.toString()
        val mid = midFromDom.ifBlank { decodeMidFromWorkUrl(workUrl) }

        if (mid.isBlank()) throw Exception("找不到漫畫 ID（mid）")

        val chapters = mutableListOf<SChapter>()
        var page = 1

        while (page <= 200) {
            val api = "$apiBase/v1/manga/chapters".toHttpUrl().newBuilder()
                .addQueryParameter("mid", mid)
                .addQueryParameter("page", page.toString())
                .addQueryParameter("per_page", "50")
                .addQueryParameter("order", "asc")
                .build()

            val res = client.newCall(GET(api, headers)).execute()
            val root = res.use { json.parseToJsonElement(it.body.string()).jsonObject }

            val data = root["data"]?.jsonObject ?: break
            val items = data["items"] as? JsonArray ?: JsonArray(emptyList())

            items.forEach { item ->
                val obj = item.jsonObject
                val hid = obj.string("hid")
                if (hid.isBlank()) return@forEach

                val title = obj.string("title").ifBlank { hid }

                chapters += SChapter.create().apply {
                    name = title
                    url = "https://reader.hipmh.top/chapter/$hid"
                }
            }

            val currentPage = data.int("page", page)
            val totalPages = data.int("total_pages", currentPage)

            if (items.isEmpty() || currentPage >= totalPages) break
            page++
        }

        return chapters.reversed()
    }

    private fun decodeMidFromWorkUrl(url: String): String {
        val path = url.toHttpUrl().encodedPath
        val token = path.substringAfter("/works/", "")
            .substringBefore("-", "")
            .trim()

        if (token.isBlank()) return ""

        return runCatching {
            val padded = token + "=".repeat((4 - token.length % 4) % 4)
            val decoded = String(Base64.getUrlDecoder().decode(padded))
            decoded.substringAfter("m:", "")
        }.getOrDefault("")
    }

    override fun pageListRequest(chapter: SChapter): Request =
        GET(
            chapter.url,
            headersBuilder().set("Referer", "$baseUrl/").build(),
        )

    override fun pageListParse(response: Response): List<Page> {
        val document = response.asJsoup()
        val content = document.selectFirst("#chapcontent")
            ?: throw Exception("找不到章節圖片設定 #chapcontent")

        val apiHid = content.attr("data-api-hid")
        if (apiHid.isBlank()) throw Exception("找不到 data-api-hid")

        val apiFromPage = content.attr("data-api-base-url").trimEnd('/')
        val chapterApiBase = if (apiFromPage.isNotBlank()) apiFromPage else apiBase

        val apiUrl = if (chapterApiBase.endsWith("/v2")) {
            "$chapterApiBase/chapter?hid=$apiHid"
        } else {
            "$chapterApiBase/v2/chapter?hid=$apiHid"
        }

        val apiResponse = client.newCall(
            GET(
                apiUrl,
                headersBuilder()
                    .set("Referer", "https://reader.hipmh.top/")
                    .build(),
            ),
        ).execute()

        val root = apiResponse.use {
            json.parseToJsonElement(it.body.string()).jsonObject
        }

        val data = root["data"]?.jsonObject
            ?: throw Exception("章節 API 沒有 data")

        val imageBase = sequenceOf(
            content.attr("data-chapter-img-base-line1"),
            content.attr("data-chapter-img-base"),
            data.string("chapter_img_base"),
            data.string("chapterImgBase"),
        ).firstOrNull { it.isNotBlank() }.orEmpty()

        val imagesElement = data["images"]

        val urls = when (imagesElement) {
            is JsonArray -> imagesElement.mapNotNull { imageUrlFromElement(it, imageBase) }

            is JsonObject -> {
                val arr = imagesElement["images"] as? JsonArray
                arr?.mapNotNull { imageUrlFromElement(it, imageBase) }.orEmpty()
            }

            is JsonPrimitive -> {
                if (imagesElement.contentOrNull.isNullOrBlank()) {
                    emptyList()
                } else {
                    throw Exception("此章節使用 HipMH 加密圖片清單，下一版需加入 chapter-decoder")
                }
            }

            else -> emptyList()
        }

        if (urls.isEmpty()) throw Exception("沒有取得漫畫圖片")

        return urls.distinct().mapIndexed { index, url ->
            Page(index, imageUrl = url)
        }
    }

    private fun imageUrlFromElement(element: JsonElement, base: String): String? {
        val raw = when (element) {
            is JsonPrimitive -> element.contentOrNull
            is JsonObject -> sequenceOf("url", "src", "img", "image", "path")
                .mapNotNull { key -> element[key]?.jsonPrimitive?.contentOrNull }
                .firstOrNull { it.isNotBlank() }
            else -> null
        }?.trim().orEmpty()

        if (raw.isBlank()) return null
        if (raw.startsWith("http://") || raw.startsWith("https://")) return raw

        return when {
            base.isBlank() -> raw
            base.endsWith("/") && raw.startsWith("/") -> base.dropLast(1) + raw
            !base.endsWith("/") && !raw.startsWith("/") -> "$base/$raw"
            else -> base + raw
        }
    }

    override fun imageRequest(page: Page): Request =
        GET(
            page.imageUrl!!,
            headersBuilder()
                .set("Referer", "https://reader.hipmh.top/")
                .build(),
        )

    override fun imageUrlParse(response: Response): String =
        throw UnsupportedOperationException()

    override fun getMangaUrl(manga: SManga): String =
        if (manga.url.startsWith("http")) manga.url else "$baseUrl${manga.url}"

    override fun getChapterUrl(chapter: SChapter): String = chapter.url

    private fun JsonObject.string(key: String): String =
        this[key]?.jsonPrimitive?.contentOrNull.orEmpty()

    private fun JsonObject.int(key: String, default: Int): Int =
        this[key]?.jsonPrimitive?.intOrNull ?: default
}
'''

(newpkg / "Hipmh.kt").write_text(hipmh_kt, encoding="utf-8")

print("HipMH v21 source prepared:", newpkg / "Hipmh.kt")
