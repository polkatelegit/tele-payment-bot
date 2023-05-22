import os
import aiogram
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ParseMode
from aiogram import types, executor
import qrcode
import asyncio
import requests
from datetime import datetime
import uuid
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import aioschedule


API_TOKEN = '5639332006:AAGOolvXWUaJnJpVOf1QBrrj0PRn0hiRGgQ'
COINBASE_API = '0c127e3d-75af-4631-b42e-63f3f01e0a12'

bot = aiogram.Bot(API_TOKEN)
dp = aiogram.Dispatcher(bot)

# Db connection

cred = credentials.Certificate('firebase_key.json')
firebase_admin.initialize_app(
    cred, {'storageBucket': 'telepaymentdb.appspot.com'})

bucket = storage.bucket()
firebase_folder_path = "pictures/"
db = firestore.client()


# Data
users = {}
products = {'prds':{}}
payments_data ={}
temp_prds =[]
ADMIN_ID = 5778351494


# Buttons
tbilisi_button = InlineKeyboardButton(text="Tbilisi", callback_data='tbilisi')
batumi_button = InlineKeyboardButton(text="Batumi", callback_data="batumi")
kutaisi_button = InlineKeyboardButton(text="Kutaisi", callback_data='kutaisai')

main_keyboard = InlineKeyboardMarkup().add(
    tbilisi_button, batumi_button, kutaisi_button)

# Start command

@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    userID = str(message.chat.id)
    if not userID in users:
        users[userID] = {}
        users[userID]['username'] = message.from_user.username
        users[userID]['name'] = message.from_user.first_name
        users[userID]['globe_state'] = ""
        users[userID]['state'] = ""
        users[userID]['temp_pid'] = ""
    else:
        users[userID]['globe_state'] = ""
        users[userID]['state'] = ""
        users[userID]['temp_pid'] = ""
    await message.reply("Welcome to the bot!!!\n\nSelect from the this list.",reply_markup=main_keyboard)
    await write_db(users, 'users')
    await write_db(products, 'products')


@dp.message_handler(commands=['showproducts'])
async def showproducts(message: Message):
    userID = str(message.chat.id)
    users[userID]['globe_state'] = ''
    users[userID]['state'] = ''
    users[userID]['temp_pid'] = ''
    res_message = "Select any one from this"
    await message.reply(text=res_message, reply_markup=main_keyboard)


@dp.message_handler(commands=['editproducts'])
async def manage_products(message:Message):
    userID = str(message.chat.id)
    users[userID]['globe_state'] = ''
    users[userID]['state'] = ''
    users[userID]['temp_pid'] = ''
    if userID == str(ADMIN_ID):

        tbilisi_button = InlineKeyboardButton(text="Tbilisi", callback_data='tbilisi_edit')
        batumi_button = InlineKeyboardButton(text="Batumi", callback_data="batumi_edit")
        kutaisi_button = InlineKeyboardButton(text="Kutaisi", callback_data='kutaisai_edit')

        manage_prdocuts_keyboard = InlineKeyboardMarkup().add(tbilisi_button, batumi_button, kutaisi_button)
        await message.reply(text="Please select product category.",reply_markup=manage_prdocuts_keyboard)



@dp.message_handler(commands=['addproduct'])
async def add_product(message: Message):
    userID = str(message.chat.id)
    users[userID]['globe_state'] = ''
    users[userID]['state'] = ''
    users[userID]['temp_pid'] = ''
    if userID == str(ADMIN_ID):
        users[userID]['globe_state'] = 'add_product'
        users[userID]['state'] = 'waiting_for_product_name'
        await message.reply("Please enter the product name")


@dp.message_handler(content_types=[types.ContentType.TEXT, types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def normal_message_handler(message: Message):
    userID = str(message.chat.id)
    if userID in users:
        if users[userID]['globe_state'] == 'add_product':
            if users[userID]['state'] == "waiting_for_product_name":
                if message.content_type == types.ContentType.TEXT:
                    current_time = datetime.now()
                    unique_id = f'{(str(uuid.uuid4())[:9])}{current_time.strftime("%H%M%S")}'
                    products['prds'][unique_id] = {}
                    products['prds'][unique_id]['product_id'] = unique_id
                    users[userID]['temp_pid'] = unique_id
                    product_name = message.text
                    products['prds'][unique_id]['name'] = product_name
                    users[userID]['state'] = "waiting_for_product_description"
                    await message.reply("Please enter the product description")

            elif users[userID]['state'] == "waiting_for_product_description":
                p_id = users[userID]['temp_pid']
                if message.content_type == types.ContentType.TEXT:
                    product_description = message.text
                    products['prds'][p_id]['description'] = product_description
                    users[userID]['state'] = "waiting_for_product_price"
                    await message.reply("Please enter the product price")

            elif users[userID]['state'] == "waiting_for_product_price":
                p_id = users[userID]['temp_pid']
                if message.content_type == types.ContentType.TEXT:
                    try:
                        product_price = int(message.text)
                        products['prds'][p_id]['price'] = product_price
                        users[userID]['state'] = "waiting_for_product_category"

                        tbilisi_button = InlineKeyboardButton(
                            text="Tbilisi", callback_data='tbilisi_cat')
                        batumi_button = InlineKeyboardButton(
                            text="Batumi", callback_data="batumi_cat")
                        kutaisi_button = InlineKeyboardButton(
                            text="Kutaisi", callback_data='kutaisai_cat')
                        category_keyboard = InlineKeyboardMarkup(row_width=1).add(
                            tbilisi_button, batumi_button, kutaisi_button)
                        await message.reply(text="Please select the product category", reply_markup=category_keyboard)
                    except Exception as e:
                        await message.reply("Please enter a valid number for price.")
                        print(f"Product price error : {e}")

            elif users[userID]['state'] == "waiting_for_product_image":
                p_id = users[userID]['temp_pid']
                if message.content_type == types.ContentType.PHOTO:
                    picture = message.photo[-1]
                    picture_name = f'{p_id}.jpg'
                    picture_path = f'pictures/{picture_name}'
                    products['prds'][p_id]['picture_name'] = picture_name
                    await bot.download_file_by_id(picture.file_id, picture_path)
                    firebase_storage_path = firebase_folder_path+picture_name
                    blob = bucket.blob(firebase_storage_path)
                    blob.upload_from_filename(picture_path)
                    users[userID]['globe_state'] = ''
                    users[userID]['state'] = ''
                    users[userID]['temp_pid'] = ''
                    await message.reply("Product added successfully.")
                else:
                    await message.reply("Please send a valid photo.")
        elif users[userID]['globe_state'] == "edit_product":
            if users[userID]['state'] =="waiting_for_new_name":
                p_id = users[userID]['temp_pid']
                product_name =  message.text
                products['prds'][p_id]['name'] = product_name

                name_callback = f'nam_{p_id}'
                des_callback = f"des_{p_id}"
                price_callback = f"pri_{p_id}"
                picture_callback = f"pic_{p_id}"
        
                name_button =InlineKeyboardButton(text="Name",callback_data=name_callback)
                description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,description_button,price_button,picture_button,back_button)

                users[userID]['globe_state'] = ''
                users[userID]['state'] = ''
                users[userID]['temp_pid'] = ''
                await message.reply("Name changed successfully",reply_markup=edit_keyboard)
                

            elif users[userID]['state'] =="waiting_for_new_description":
                p_id = users[userID]['temp_pid']
                product_description = message.text
                products['prds'][p_id]['description'] =product_description

                name_callback = f'nam_{p_id}'
                des_callback = f"des_{p_id}"
                price_callback = f"pri_{p_id}"
                picture_callback = f"pic_{p_id}"
        
                name_button =InlineKeyboardButton(text="Name",callback_data=name_callback)
                description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,description_button,price_button,picture_button,back_button)
                
                users[userID]['globe_state'] = ''
                users[userID]['state'] = ''
                users[userID]['temp_pid'] = ''
                await message.reply("Description changed successfully.",reply_markup=edit_keyboard)
            
            elif users[userID]['state'] =="waiting_for_new_price":
                p_id = users[userID]['temp_pid']
                try:
                    product_price = int(message.text)
                    products['prds'][p_id]['price'] = product_price


                    name_callback = f'nam_{p_id}'
                    des_callback = f"des_{p_id}"
                    price_callback = f"pri_{p_id}"
                    picture_callback = f"pic_{p_id}"
            
                    name_button =InlineKeyboardButton(text="Name",callback_data=name_callback)
                    description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                    price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                    picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                    back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                    edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,description_button,price_button,picture_button,back_button)
                    users[userID]['globe_state'] = ''
                    users[userID]['state'] = ''
                    users[userID]['temp_pid'] = ''
                    await message.reply("Price saved successfully.",reply_markup=edit_keyboard)

                except Exception as e:
                    await message.reply("Please enter a valid number for price.")
            elif users[userID]['state'] =="waiting_for_new_picture":
                p_id = users[userID]['temp_pid']
                if message.content_type == types.ContentType.PHOTO:
                    if not products['prds'][p_id]["picture_name"] == "":
                        firebase_storage_path = firebase_folder_path+products['prds'][p_id]["picture_name"]
                        try:
                            blob = bucket.blob(firebase_storage_path)
                            blob.delete()
                        except Exception as e:
                            print(f"Error while changing the image : {e}")
                        if os.path.exists(f'pictures/{products["prds"][p_id]["picture_name"]}'):
                            os.remove(f'pictures/{products["prds"][p_id]["picture_name"]}')
                        products['prds'][p_id]['picture_name']=""
                    picture = message.photo[-1]
                    picture_name = f'{p_id}.jpg'
                    picture_path = f'pictures/{picture_name}'
                    products['prds'][p_id]['picture_name'] =picture_name
                    await bot.download_file_by_id(picture.file_id,picture_path)
                    firebase_storage_path= firebase_folder_path +picture_name
                    try:
                        blob = bucket.blob(firebase_storage_path)
                        blob.upload_from_filename(firebase_storage_path)
                    except Exception as e:
                        print(f"Error while uploading image : {e}")

                    name_callback = f'nam_{p_id}'
                    des_callback = f"des_{p_id}"
                    price_callback = f"pri_{p_id}"
                    picture_callback = f"pic_{p_id}"
            
                    name_button =InlineKeyboardButton(text="Name",callback_data=name_callback)
                    description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                    price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                    picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                    back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                    edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,description_button,price_button,picture_button,back_button)
                    

                    users[userID]['globe_state'] = ''
                    users[userID]['state'] = ''
                    users[userID]['temp_pid'] = ''
                    await message.reply("Picture saved successfully.",reply_markup=edit_keyboard)
            
        
    await write_db(users, 'users')
    await write_db(products, 'products')


@dp.callback_query_handler()
async def query_handler(call: CallbackQuery):
    userID = str(call.message.chat.id)
    if userID in users:
        product_ids = []
        for product in products['prds']:
            if len(products['prds']) > 0:
                product_ids.append(products['prds'][product]['product_id'])

        call_data = call.data
        prefix = ""
        suff_ID = ""
        prefix = call_data[:4]
        suff_ID = call_data[4:]
        

        if prefix != "" and suff_ID != "":
            if (prefix == "buy_") and suff_ID in product_ids:
                if (not products['prds'][suff_ID]['picture_name'] =="") and (not suff_ID in temp_prds) :
                    temp_prds.append(suff_ID)
                    await read_db(payments_data,'payments_data')
                    amount = products['prds'][suff_ID]['price']
                    order_id = f'{userID}_{suff_ID}'
                    res_dict = await create_charge(amount=amount, userID=userID, orderID=order_id, p_ID=suff_ID)
                    if not userID in payments_data:
                        payments_data[userID]={}
  
                    payments_data[userID][res_dict['c_id']]={}
                    payments_data[userID][res_dict['c_id']]={"c_id":res_dict['c_id'],"creation_time":res_dict['creation_time'],"expiring_time":res_dict['expiring_time'],"status":"created","sub_status":"","amount":res_dict['amount_to_send'],'p_id':suff_ID}
                    
                    # Generating QR code
                    qr = qrcode.QRCode(
                        version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4
                    )
                    
                    qr_data = res_dict['receiving_address']
                    qr.add_data(qr_data)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")
                    img_name = f"{res_dict['receiving_address']}_qr.png"
                    img.save(img_name)

                    payment_callback = f'pay_{res_dict["c_id"]}'
                    cancel_callback = f'can_{res_dict["c_id"]}'
                    payment_confirm_button = InlineKeyboardButton(text="✔️Confirm",callback_data=payment_callback)
                    cancel_confirm_button = InlineKeyboardButton(text="❌Cancel",callback_data=cancel_callback)
                    payment_keyboard = InlineKeyboardMarkup(row_width=2).add(payment_confirm_button,cancel_confirm_button)

                    res_message = f"Payment Details :\n\nAmount💵 : <code>{res_dict['amount_to_send']}</code> <b>LTC</b> \nAddress : <code>{res_dict['receiving_address']}</code>\n\nPlease send the exact amount of LTC to this address.If any fees are applicable then make to sure to add that.\n\n⚠️You have one hour to send the amount after that address will expire⚠️. \n\nOnce you have completed the payment click on confirm payment."
                    with open(img_name, 'rb') as qrfile:
                        await bot.send_photo(userID, qrfile, caption=res_message, parse_mode=ParseMode.HTML,reply_markup=payment_keyboard)

                    if os.path.exists(img_name):
                        os.remove(img_name)
                    await write_db(payments_data,'payments_data')
                else:
                    res_message = "It is out of stock now.Please check after some time"
                    await call.message.answer(text=res_message)
                # await call.message.answer(text=res_message,parse_mode=ParseMode.HTML)
            elif (prefix == "pay_"):
                c_id = suff_ID
                await read_db(payments_data,'payments_data')
                payment_dict =payments_data[userID][c_id]
                if payment_dict['status'] == "pending" or payment_dict['status'] == "created":
                    check_status_callback = f"che_{c_id}"
                    check_status_button = InlineKeyboardButton("🔄️Check Status",callback_data=check_status_callback)
                    check_status_keyboard = InlineKeyboardMarkup().add(check_status_button)
                    res_message = "Please wait some time.Confirmation is pending on network.\n\n⚠️Please do not use any command or message.Wait till confirmation is completed.⚠️"
                    await call.message.answer(text=res_message,reply_markup=check_status_keyboard)
                
                elif payment_dict['status'] == "confirmed":
                    p_id = payments_data[userID][c_id]['p_id']
                    await send_picture(userID,c_id,p_id)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


                elif payment_dict['status'] == "failed":
                    p_id = payments_data[userID][c_id]['p_id']
                    substatus =  payments_data[userID][c_id]['sub_status']
                    if substatus == "underpaid":
                        await bot.send_message(chat_id=userID,text="You have underpaid the amount. Please go and purchase again with the correct amount or contact the admin for refund.")
                        if p_id in temp_prds:
                            temp_prds.remove(p_id)
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    elif substatus =="expired":
                        await bot.send_message(chat_id=userID,text="Address is expired. Please go to main menu again and purchase again and make sure to complete payment within 1 hour.")
                        if p_id in temp_prds:
                            temp_prds.remove(p_id)
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            elif (prefix =="che_"):
                c_id =  suff_ID
                pay_dict = await check_payment_status(userID,c_id)
                if pay_dict['status'] == "pending" or pay_dict['status'] == "created":
                    check_status_callback = f"che_{c_id}"
                    check_status_button = InlineKeyboardButton("🔄️Check Status",callback_data=check_status_callback)
                    check_status_keyboard = InlineKeyboardMarkup().add(check_status_button)
                    res_message = "Please wait some time.Confirmation is pending on network.\n\n⚠️Please do not use any command or send any message.Wait till confirmation is completed.⚠️"
                    await call.message.answer(text=res_message,reply_markup=check_status_keyboard)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif pay_dict['status'] == "confirmed":
                    p_id = payments_data[userID][c_id]['p_id']
                    await send_picture(userID,c_id,p_id)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif pay_dict['status'] == "failed":
                    p_id = payments_data[userID][c_id]['p_id']
                    substatus =  pay_dict['sub_status']
                    if substatus == "underpaid":
                        await bot.send_message(chat_id=userID,text="You have underpaid the amount. Please go and purchase again with the correct amount or contact the admin for refund.")
                        if p_id in temp_prds:
                            temp_prds.remove(p_id)
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    elif substatus =="expired":
                        await bot.send_message(chat_id=userID,text="Address is expired. Please go to main menu again and purchase again and make sure to complete payment within 1 hour.")
                        if p_id in temp_prds:
                            temp_prds.remove(p_id)
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            elif (prefix == "can_"):
                c_id =  suff_ID
                p_id = payments_data[userID][c_id]['p_id']
                if p_id in temp_prds:
                    temp_prds.remove(p_id)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            elif (prefix == "man_"):
                p_id = suff_ID
                res_message ="Select what you want to do"
                edit_callback = f"edi_{p_id}"
                delete_callback =f"del_{p_id}"
                edit_product_button = InlineKeyboardButton(text="Edit",callback_data=edit_callback)
                delete_product_button = InlineKeyboardButton(text="Delete",callback_data=delete_callback)

                if p_id in products['prds']:
                    category = products['prds'][p_id]['category']
                
                if  category =="tbilisi":
                    back_to_product_list =  InlineKeyboardButton(text="⬅️Back",callback_data="tbilisi_edit")
                elif category =="batumi":
                    back_to_product_list =  InlineKeyboardButton(text="⬅️Back",callback_data="batumi_edit")
                elif category =="kutaisai":
                    back_to_product_list =  InlineKeyboardButton(text="⬅️Back",callback_data="kutaisai_edit")

                manage_products_keyboard = InlineKeyboardMarkup(row_width=2).add(edit_product_button,delete_product_button,back_to_product_list)
                await call.message.answer(text=res_message,reply_markup=manage_products_keyboard)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                

            elif (prefix == "edi_"):
                p_id=suff_ID
                res_message ="Choose what you want to update."

                name_callback = f'nam_{p_id}'
                des_callback = f"des_{p_id}"
                price_callback = f"pri_{p_id}"
                picture_callback = f"pic_{p_id}"
        
                name_button =InlineKeyboardButton(text="Name",callback_data=name_callback)
                description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,description_button,price_button,picture_button,back_button)
                users[userID]['globe_state'] = ''
                users[userID]['state'] = ''
                users[userID]['temp_pid'] = ''
                await call.message.answer(text=res_message,reply_markup=edit_keyboard)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            elif (prefix =="nam_"):
                p_id = suff_ID
                res_message = f"Current product name is <b>{products['prds'][p_id]['name']}</b>,Please send the new name which you want to save."
                res_button =  InlineKeyboardButton(text="⬅️Back",callback_data=f'edi_{p_id}')
                res_keyboard = InlineKeyboardMarkup().add(res_button)
                users[userID]['globe_state'] = "edit_product"
                users[userID]['state'] = "waiting_for_new_name"
                users[userID]['temp_pid'] =p_id
                await call.message.answer(text=res_message,reply_markup=res_keyboard,parse_mode=ParseMode.HTML)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                
            elif (prefix =="des_"):
                p_id = suff_ID
                res_message = f"Current description is <b>{products['prds'][p_id]['description']}</b>,please send the new description you want to save"
                res_button =  InlineKeyboardButton(text="⬅️Back",callback_data=f'edi_{p_id}')
                res_keyboard = InlineKeyboardMarkup().add(res_button)
                users[userID]['globe_state'] = "edit_product"
                users[userID]['state'] = "waiting_for_new_description"
                users[userID]['temp_pid'] = p_id
                await call.message.answer(text=res_message,reply_markup=res_keyboard,parse_mode=ParseMode.HTML)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            elif (prefix =="pri_"):
                p_id = suff_ID
                res_message = f"Current Price is $<b>{products['prds'][p_id]['price']}</b>,please send the new price you want to save"
                res_button =  InlineKeyboardButton(text="⬅️Back",callback_data=f'edi_{p_id}')
                res_keyboard = InlineKeyboardMarkup().add(res_button)
                users[userID]['globe_state'] = "edit_product"
                users[userID]['state'] = "waiting_for_new_price"
                users[userID]['temp_pid'] = p_id
                await call.message.answer(text=res_message,reply_markup=res_keyboard,parse_mode=ParseMode.HTML)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            
            elif (prefix =="pic_"):
                p_id = suff_ID
                if not products['prds'][p_id]['picture_name'] == "":
                    res_message = f"Current Picture is <b>{products['prds'][p_id]['picture_name']}</b>,please send the new picture you want to save"
                else : 
                    res_message = f"This picture is sold,please send the new picture you want to save"

                res_button =  InlineKeyboardButton(text="⬅️Back",callback_data=f'edi_{p_id}')
                res_keyboard = InlineKeyboardMarkup().add(res_button)
                users[userID]['globe_state'] = "edit_product"
                users[userID]['state'] = "waiting_for_new_picture"
                users[userID]['temp_pid'] = p_id
                await call.message.answer(text=res_message,reply_markup=res_keyboard,parse_mode=ParseMode.HTML)
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

            elif (prefix == "del_"):
                p_id =suff_ID
                if p_id in products['prds']:
                    if len(products['prds'][p_id])>=6:
                        picture_name = products['prds'][p_id]['picture_name']
                        if not picture_name=="": 
                            try:
                                firebase_store_path = firebase_folder_path+picture_name
                                blob= bucket.blob(firebase_store_path)
                                blob.delete()
                                if os.path.exists(f'pictures/{picture_name}'):
                                    os.remove(f'pictures/{picture_name}')
                            except Exception as e:
                                print(f"Error in deleting from bucket : {e}")
                    try:
                        del products['prds'][p_id]
                    except Exception as e:
                        print(f"Error in deleting product from db")
                    await call.message.answer("Product deleted successfully.")
                else:
                    await call.message.answer("Product is already deleted.")


        if call.data in product_ids:
            res_message = f"Name : {products['prds'][call.data]['name']}\nDescription : {products['prds'][call.data]['description']}\nPrice : ${products['prds'][call.data]['price']}"
            call_back_data = f"buy_{call.data}"
            buy_button = InlineKeyboardButton(
                text="Buy", callback_data=call_back_data)
            category = products['prds'][call.data]['category']
            if category == "tbilisi":
                back_btn = InlineKeyboardButton(
                    text="⬅️Back", callback_data="tbilisi")
            elif category == "batumi":
                back_btn = InlineKeyboardButton(
                    text="⬅️Back", callback_data="batumi")
            elif category == "kutaisai":
                back_btn = InlineKeyboardButton(
                    text="⬅️Back", callback_data="kutaisai")

            pd_keyboard = InlineKeyboardMarkup().add(buy_button, back_btn)
            await call.message.reply(text=res_message, reply_markup=pd_keyboard)
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        else:

            if users[userID]['globe_state'] == 'add_product':
                p_id = users[userID]['temp_pid']
                if users[userID]['state'] == "waiting_for_product_category":
                    if call.data == "tbilisi_cat":
                        products['prds'][p_id]['category'] = 'tbilisi'
                        users[userID]['state'] = "waiting_for_product_image"
                        await call.message.answer(text="Please send the picture of product.")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    elif call.data == "batumi_cat":
                        products['prds'][p_id]['category'] = 'batumi'
                        users[userID]['state'] = "waiting_for_product_image"
                        await call.message.answer(text="Please send the picture of product.")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    elif call.data == "kutaisai_cat":
                        products['prds'][p_id]['category'] = 'kutaisai'
                        users[userID]['state'] = "waiting_for_product_image"
                        await call.message.answer(text="Please send the picture of product.")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            else:
                if call.data == "tbilisi":
                    await show_products(category="tbilisi", message=call.message)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif call.data == "batumi":
                    await show_products(category="batumi", message=call.message)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif call.data == "kutaisai":
                    await show_products(category="kutaisai", message=call.message)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        
                elif call.data == "back_to_main_menu":
                    res_message = "Select any one from this"
                    await call.message.answer(text=res_message, reply_markup=main_keyboard)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif call.data =="tbilisi_edit":
                    await display_edit_products(category="tbilisi",message=call.message)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif call.data =="batumi_edit":
                    await display_edit_products(category="batumi",message=call.message)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                elif call.data =="kutaisai_edit":
                    await display_edit_products(category="kutaisai",message=call.message)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                
                elif call.data == "back_to_manage_product":
                    tbilisi_button = InlineKeyboardButton(text="Tbilisi", callback_data='tbilisi_edit')
                    batumi_button = InlineKeyboardButton(text="Batumi", callback_data="batumi_edit")
                    kutaisi_button = InlineKeyboardButton(text="Kutaisi", callback_data='kutaisai_edit')

                    manage_prdocuts_keyboard = InlineKeyboardMarkup().add(tbilisi_button, batumi_button, kutaisi_button)
                    await call.message.answer(text="Please select product category.",reply_markup=manage_prdocuts_keyboard)
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


    await write_db(users, 'users')
    await write_db(products, 'products')

async def display_edit_products(category,message):
    buttons=[]
    for product in products['prds']:
        if len(products['prds'][product])>=6:
            if products['prds'][product]['category'] == category:
                manage_callback =f'man_{products["prds"][product]["product_id"]}'
                button = InlineKeyboardButton(text=f"{products['prds'][product]['name']}",callback_data=manage_callback)
                buttons.append(button)
    back_button = InlineKeyboardButton(text="⬅️Back",callback_data="back_to_manage_product")
    buttons.append(back_button)
    products_keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await message.reply(text="Select the product from below list which you want to edit.",reply_markup =products_keyboard)


async def send_picture(userID,c_id,p_id):
    picture_path = f"pictures/{products['prds'][p_id]['picture_name']}"
    if os.path.exists(picture_path):
        with open(picture_path,'rb') as picture:
            await bot.send_photo(chat_id=userID,photo=picture)

    if os.path.exists(picture_path):
        os.remove(picture_path)
    try:
        firebase_storage_path =  firebase_folder_path+products['prds'][p_id]['picture_name']
        blob = bucket.blob(firebase_storage_path)
        blob.delete()
    except Exception as e:
        print(f"Error in deleting from bucket : {e}") 
    products['prds'][p_id]['picture_name']=""
    if p_id in temp_prds:
        temp_prds.remove(p_id)
    await write_db(products,"products")

async def check_payment_status(userID,c_id):
    await read_db(payments_data,'payments_data')
    print(c_id)
    payment_dict = payments_data[userID][c_id]
    response_dict = {
        "status":"",
        "sub_status":""
    }   
    print(payment_dict['status'])
    if payment_dict['status'] == "pending" or payment_dict['status'] == "created":
        response_dict['status'] ="pending"
        return response_dict
    elif payment_dict['status'] == "confirmed":
        response_dict['status'] ="confirmed"
        return response_dict
    elif payment_dict['status'] == "failed":
        response_dict['status'] = "failed"
        response_dict['sub_status'] = payment_dict['sub_status']
        return response_dict

async def create_charge(amount, userID, orderID, p_ID):
    url = "https://api.commerce.coinbase.com/charges"
    headers = {
        'X-CC-Api-Key': COINBASE_API,
        'X-CC-Version': '2018-03-22',
        'Content-Type': 'application/json',
    }
    payload = {
        "name": f'{products["prds"][p_ID]["name"]}',
        "description": f'{products["prds"][p_ID]["description"]}',
        "local_price": {
            "amount": amount,
            "currency": "USD",
        },
        "pricing_type": "fixed_price",
        "metadata": {
            'user_id': userID,
            'order_id': orderID,
        }
    }
    response = requests.post(url=url, json=payload, headers=headers)
    if response.status_code == 201:
        charge = response.json()
        response_dict = {}
        response_dict['c_id'] = charge['data']['id']
        response_dict['receiving_address'] = charge['data']['addresses']['litecoin']
        response_dict['amount_to_send'] = charge['data']['pricing']['litecoin']['amount']
        response_dict['creation_time'] = charge['data']['created_at']
        response_dict['expiring_time'] = charge['data']['expires_at']
    return response_dict

async def show_products(category, message):
    buttons = []
    for product in products['prds']:
        if len(products['prds'][product])>=6:
            if products['prds'][product]['category'] == category:
                button = InlineKeyboardButton(
                    text=f'{products["prds"][product]["name"]}', callback_data=f'{products["prds"][product]["product_id"]}')
                buttons.append(button)
    back_button = InlineKeyboardButton(
        text="⬅️Back", callback_data="back_to_main_menu")
    buttons.append(back_button)
    products_keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await message.reply(text="Select from this list.", reply_markup=products_keyboard)

async def check_status_of_pids():
    await read_db(payments_data,'payments_data')
    for user in payments_data:
        user_payments = payments_data[user]
        for payment in user_payments:
            if user_payments[payment]['status'] =="failed":
                if user_payments[payment]['sub_status'] =="expired":
                    p_id = user_payments[payment]['p_id']
                    if p_id in temp_prds:
                        temp_prds.remove(p_id)

async def download_images():

    for product in products['prds']:
        if len(products['prds'][product])>=6:
            if not products['prds'][product]['picture_name'] == "":
                try:
                    picture_name = products['prds'][product]['picture_name']
                    local_path = f'pictures/{picture_name}'
                    firebase_storage_path = firebase_folder_path + products['prds'][product]['picture_name']
                    blob = bucket.blob(firebase_storage_path)
                    blob.download_to_filename(local_path)
                except Exception as e:
                    print(f"Error in downloading images.{e}")


async def write_db(wDictonary, dict_name):
    try:
        for key, value in wDictonary.items():
            doc_ref = db.collection(dict_name).document(key)
            doc_ref.set(value)
    except Exception as e:
        print(f"Error in DB update {e}")


async def read_db(wDictonary, dict_name):
    data_ref = db.collection(dict_name)
    data_docs = data_ref.get()

    for doc in data_docs:
        wDictonary[doc.id] = doc.to_dict()

async def  hourly_checker():
    aioschedule.every().hour.do(check_status_of_pids)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(100)


# Webhook Hitter
async def webhook_hitter():
    webhook_url = "https://polkabot-telegrampaymentbot.b4a.run/"
    while True:
        try:
            response = requests.get(webhook_url)
            if response.status_code ==200:
                print("Website is alive ")
            else:
                print("Website returned a non-200 status code:",response.status_code)
        except Exception as e:
            print(f"Error in webhook : {e}")

        await asyncio.sleep(250)


async def main(_):
    await read_db(users, 'users')
    await read_db(products, 'products')
    await download_images()
    asyncio.create_task(hourly_checker())
    asyncio.create_task(webhook_hitter())

    print("Bot is started..")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=main)
