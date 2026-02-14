import requests
import io
from PIL import Image
from bs4 import BeautifulSoup

def download_image(url: str) -> dict:
    try:
        # Check for Instagram URL and try to extract direct image
        if "instagram.com" in url:
            try:
                # Add /media/?size=l if it's a post URL
                if "/p/" in url or "/reels/" in url:
                    # Strip query params and add media suffix
                    base_url = url.split("?")[0]
                    if not base_url.endswith("/"):
                        base_url += "/"
                    media_url = base_url + "media/?size=l"
                    
                    print(f"📸 Detected Instagram URL, attempting to fetch from: {media_url}")
                    
                    media_resp = requests.get(
                        media_url,
                        timeout=5,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                        },
                        allow_redirects=True
                    )
                    
                    if media_resp.status_code == 200 and "image" in media_resp.headers.get("Content-Type", ""):
                        # Verify it's a valid image
                        img = Image.open(io.BytesIO(media_resp.content))
                        img.verify()
                        return {
                            "success": True,
                            "buffer": media_resp.content
                        }
            except Exception as ig_err:
                print(f"⚠️ Instagram direct extraction failed: {str(ig_err)}")
                # Continue with normal download as fallback

        response = requests.get(
            url,
            timeout=5,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        response.raise_for_status()
        
        # Check if it's an image
        content_type = response.headers.get("Content-Type", "").lower()
        if "image" not in content_type:
            # If it's not an image, it might be a page we can scrape for og:image
            try:
                soup = BeautifulSoup(response.content, 'html.parser')
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    print(f"🔗 Found og:image: {og_image['content']}")
                    return download_image(og_image["content"])
            except Exception as scrape_err:
                print(f"⚠️ Scrape attempt failed: {str(scrape_err)}")
            
            return {
                "success": False,
                "error": f"URL did not return an image (Content-Type: {content_type})"
            }

        # Verify it's a valid image using Pillow
        try:
            img = Image.open(io.BytesIO(response.content))
            img.verify()
        except Exception as img_err:
            return {
                "success": False,
                "error": f"Downloaded data is not a valid image: {str(img_err)}"
            }
            
        return {
            "success": True,
            "buffer": response.content
        }
    except requests.Timeout:
        error_message = "Image download timed out after 5 seconds"
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            error_message = f"Failed to download image: HTTP {e.response.status_code}"
        else:
            error_message = f"Failed to download image: {str(e)}"
    except Exception as e:
        error_message = f"Failed to download image: {str(e)}"
    
    print(f"[Image Download Error] {url}: {error_message}")
    
    return {
        "success": False,
        "error": error_message
    }
