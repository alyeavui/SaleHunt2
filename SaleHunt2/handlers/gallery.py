from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import get_discounts, cart  

def gallery_buttons(index, total):
    buttons = []
    
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"prev_{index}"))
    if index < total - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"next_{index}"))
    
    buttons.append(InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_{index}"))
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

gallery_router = Router()

@gallery_router.callback_query()
async def handle_gallery(callback: CallbackQuery):
    user_id = callback.from_user.id
    action, index = callback.data.split("_")
    index = int(index)
    
    category = "Food"  
    
    discounts = await get_discounts(category)  
    if not discounts:
        return
    
    if action == "next":
        index += 1
    elif action == "prev":
        index -= 1
    elif action == "add":
        cart.setdefault(user_id, []).append(discounts[index])
        await callback.answer("Added to cart! 🛒")
        return
    
    discount = discounts[index]
    text = f"**{discount['title']}**\n\n{discount['description']}\n\n[View Deal]({discount['link']})"
    
    await callback.message.edit_media(
        types.InputMediaPhoto(media=discount['image_url'], caption=text),
        reply_markup=gallery_buttons(index, len(discounts))
    )

    await callback.answer()
