import os,shutil
import random
import zipfile
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
# temp_prds =[]
ADMIN_ID = 5778351494


# Buttons
tbilisi_button = InlineKeyboardButton(text="Tbilisi", callback_data='tbilisi')
batumi_button = InlineKeyboardButton(text="Batumi", callback_data="batumi")
kutaisi_button = InlineKeyboardButton(text="Kutaisi", callback_data='kutaisai')
wallet_button= InlineKeyboardButton(text="Wallet", callback_data='wallet')

main_keyboard = InlineKeyboardMarkup().add(tbilisi_button, batumi_button, kutaisi_button,wallet_button)

# Start command

@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    userID = str(message.chat.id)
    if not userID in users:
        users[userID] = {}
        users[userID]['username'] = message.from_user.username
        users[userID]['name'] = message.from_user.first_name
        users[userID]['wallet_balance'] = 0 
        users[userID]['globe_state'] = ""
        users[userID]['state'] = ""
        users[userID]['temp_pid'] = ""
    else:
        users[userID]['globe_state'] = ""
        users[userID]['state'] = ""
        users[userID]['temp_pid'] = ""

    payments_data ={}
    await read_db(payments_data,'payments_data')

    if userID in payments_data['payments']:
        user_balance = payments_data['payments'][userID]['balance']
        if not user_balance == 0:
            users[userID]['wallet_balance'] += user_balance
            payments_data['payments'][userID]['balance'] =0

    tbilisi_button = InlineKeyboardButton(text="Tbilisi", callback_data='tbilisi')
    batumi_button = InlineKeyboardButton(text="Batumi", callback_data="batumi")
    kutaisi_button = InlineKeyboardButton(text="Kutaisi", callback_data='kutaisai')
    g_wallet_button= InlineKeyboardButton(text=f"Credit : ${users[userID]['wallet_balance']} / შევსება", callback_data='top_up')
    # r_wallet_button= InlineKeyboardButton(text=f"Credit : ${users[userID]['wallet_balance']} / Пополнить", callback_data='top_up')
    start_keyboard = InlineKeyboardMarkup(row_width=1).add(tbilisi_button, batumi_button, kutaisi_button,g_wallet_button,r_wallet_button)

    await message.reply("🖐️გამარჯობა / Привет",reply_markup=start_keyboard)
    await write_db(users, 'users')
    await write_db(products, 'products')
    await write_db(payments_data,"payments_data")


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
                    users[userID]['state'] = "waiting_for_product_price"
                    await message.reply("Please enter the product price")

            elif users[userID]['state'] == "waiting_for_product_price":
                p_id = users[userID]['temp_pid']
                if message.content_type == types.ContentType.TEXT:
                    try:
                        product_price = int(message.text)
                        products['prds'][p_id]['price'] = product_price
                        products['prds'][p_id]['pictures_name']=[]
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
                if message.content_type == types.ContentType.PHOTO or message.content_type == types.ContentType.DOCUMENT:
                    if message.content_type == types.ContentType.PHOTO:
                        picture = message.photo[-1]
                        picture_name = f'{p_id}_{str(uuid.uuid4())}.jpg'
                        picture_path = f'pictures/{picture_name}'
                        products['prds'][p_id]['pictures_name'].append(picture_name) 
                        await bot.download_file_by_id(picture.file_id, picture_path)
                        firebase_storage_path = firebase_folder_path+picture_name
                        blob = bucket.blob(firebase_storage_path)
                        blob.upload_from_filename(picture_path)
                        users[userID]['globe_state'] = ''
                        users[userID]['state'] = ''
                        users[userID]['temp_pid'] = ''
                        await message.reply("Product added successfully.")
                    elif message.content_type == types.ContentType.DOCUMENT:
                        file_name = message.document.file_name
                        if file_name.endswith('.zip'):
                            file_id = message.document.file_id
                            zip_file_path = f'zips/{file_name}'
                            try:
                                await bot.download_file_by_id(file_id,zip_file_path)
                                if os.path.exists(zip_file_path):
                                    try:
                                        await extract_zip_file(zip_file_path,'temp_pics/')
                                        temp_folder = 'temp_pics/'
                                        dest_folder = 'pictures/'
                                        file_names = os.listdir(temp_folder)
                                        print(file_names)
                                        image_extentions= ['.jpg', '.jpeg', '.png']
                                        image_files = [file_name for file_name in file_names if os.path.splitext(file_name)[1].lower() in  image_extentions]
                                        print(image_files)
                                        for image_file in image_files:
                                            print(image_file)
                                            current_path = os.path.join(temp_folder,image_file)
                                            new_file_name = f'{p_id}_{str(uuid.uuid4())}'+image_file
                                            products['prds'][p_id]['pictures_name'].append(new_file_name)
                                            new_path = os.path.join(dest_folder,new_file_name)
                                            shutil.copy(current_path,new_path)
                                            firebase_storage_path = firebase_folder_path+new_file_name
                                            blob = bucket.blob(firebase_storage_path)
                                            blob.upload_from_filename(new_path)
                                            
                                        os.remove(zip_file_path)
                                        await message.reply("Product added successfully.")

                                        for file_name in file_names:
                                                t_file_path = os.path.join(temp_folder, file_name)
                                                os.remove(t_file_path)

                                    except Exception as e:
                                        print(f"Error in extracting zip file: {e}")
                                        
                            except Exception as e:
                                print(f"Error in downloading zip file : {e}")
                            
                    else:
                        await message.reply("Please send a valid photo or zip file.")
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
                # description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,price_button,picture_button,back_button)

                users[userID]['globe_state'] = ''
                users[userID]['state'] = ''
                users[userID]['temp_pid'] = ''
                await message.reply("Name changed successfully",reply_markup=edit_keyboard)
                

            
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
                    # description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                    price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                    picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                    back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                    edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,price_button,picture_button,back_button)
                    users[userID]['globe_state'] = ''
                    users[userID]['state'] = ''
                    users[userID]['temp_pid'] = ''
                    await message.reply("Price saved successfully.",reply_markup=edit_keyboard)

                except Exception as e:
                    await message.reply("Please enter a valid number for price.")
            elif users[userID]['state'] =="waiting_for_new_picture":
                p_id = users[userID]['temp_pid']

                if message.content_type == types.ContentType.PHOTO or message.content_type == types.ContentType.DOCUMENT:
                    if message.content_type == types.ContentType.PHOTO:
                        picture = message.photo[-1]
                        picture_name = f'{p_id}_{str(uuid.uuid4())}.jpg'
                        picture_path = f'pictures/{picture_name}'
                        products['prds'][p_id]['pictures_name'].append(picture_name) 
                        await bot.download_file_by_id(picture.file_id, picture_path)
                        firebase_storage_path = firebase_folder_path+picture_name
                        blob = bucket.blob(firebase_storage_path)
                        blob.upload_from_filename(picture_path)
                        users[userID]['globe_state'] = ''
                        users[userID]['state'] = ''
                        users[userID]['temp_pid'] = ''
                        await message.reply("Image added successfully.")
                    
                    elif message.content_type == types.ContentType.DOCUMENT:
                        file_name = message.document.file_name
                        if file_name.endswith('.zip'):
                            file_id = message.document.file_id
                            zip_file_path = message.document.file_id
                            zip_file_path =f'zips/{file_name}'
                            try:
                                await bot.download_file_by_id(file_id,zip_file_path)
                                if os.path.exists(zip_file_path):
                                    try:
                                        await extract_zip_file(zip_file_path,'temp_pics/')
                                        temp_folder = 'temp_pics/'
                                        dest_folder = 'pictures/'
                                        file_names = os.listdir(temp_folder)
                                        image_extentions= ['.jpg', '.jpeg', '.png']
                                        image_files = [file_name for file_name in file_names if os.path.splitext(file_name)[1].lower() in  image_extentions]
                                        for image_file in image_files:
                                            current_path = os.path.join(temp_folder,image_file)
                                            new_file_name = f'{p_id}_{str(uuid.uuid4())}'+image_file
                                            products['prds'][p_id]['pictures_name'].append(new_file_name)
                                            new_path = os.path.join(dest_folder,new_file_name)
                                            shutil.copy(current_path,new_path)
                                            firebase_storage_path = firebase_folder_path+new_file_name
                                            blob = bucket.blob(firebase_storage_path)
                                            blob.upload_from_filename(new_path)
                                        os.remove(zip_file_path)
                                        await message.reply("Pictures added successfully.")

                                        for file_name in file_names:
                                                t_file_path = os.path.join(temp_folder, file_name)
                                                os.remove(t_file_path)
                                    except Exception as e:
                                                print(f"Error in extracting zip file: {e}")
                                        
                            except Exception as e:
                                print(f"Error in downloading zip file : {e}")
                    else:
                        await message.reply("Please upload valid photo or zip file.")            


                    name_callback = f'nam_{p_id}'
                    des_callback = f"des_{p_id}"
                    price_callback = f"pri_{p_id}"
                    picture_callback = f"pic_{p_id}"
            
                    name_button =InlineKeyboardButton(text="Name",callback_data=name_callback)
                    # description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                    price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                    picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                    back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                    edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,price_button,picture_button,back_button)
                    

                    users[userID]['globe_state'] = ''
                    users[userID]['state'] = ''
                    users[userID]['temp_pid'] = ''
                    await message.answer("Please select from below list.",reply_markup=edit_keyboard)
                else:
                    await message.reply("Please upload a valid photo or zip file.")
        
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
                if (len(products['prds'][suff_ID]['pictures_name'])>0) :

                    if users[userID]['wallet_balance'] > products['prds'][suff_ID]['price']:
                        await send_picture(userID,p_id=suff_ID)
                        users[userID]['wallet_balance'] = users[userID]['wallet_balance'] - products['prds'][suff_ID]['price']
                         
                    else:
                        await call.message.answer("You do not have enough balance in wallet, please use /start command and top up your wallet.")

              
                else:
                    res_message = "It is out of stock now.Please check after some time"
                    await call.message.answer(text=res_message)





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
                # description_button = InlineKeyboardButton(text="Description",callback_data=des_callback)
                price_button = InlineKeyboardButton(text="Price",callback_data=price_callback)
                picture_button = InlineKeyboardButton(text="Picture",callback_data=picture_callback)
                back_button =InlineKeyboardButton(text="⬅️Back",callback_data=f"man_{p_id}")

                edit_keyboard = InlineKeyboardMarkup(row_width=2).add(name_button,price_button,picture_button,back_button)
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
                if len(products['prds'][p_id]['pictures_name']) > 0 :
                    res_message = f"Currently there are <b>{len(products['prds'][p_id]['pictures_name'])}</b>,please send the new pictures you want to save"
                else : 
                    res_message = f"All pictures are sold, please send the new pictures you want to save"

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
                    if len(products['prds'][p_id])>=5:
                        pictures = products['prds'][p_id]['pictures_name']
                        if len(pictures)>0: 
                            try:
                                for picture in pictures:
                                    firebase_store_path = firebase_folder_path+picture
                                    blob= bucket.blob(firebase_store_path)
                                    blob.delete()
                                    if os.path.exists(f'pictures/{picture}'):
                                        os.remove(f'pictures/{picture}')
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

            res_message = f"""{products['prds'][call.data]['name']} (${products['prds'][call.data]['price']})
Wallet Credit : ${users[userID]['wallet_balance']}

ყიდვის შემდეგ კრედიტები ჩამოგეჭრება ბალანსიდან. 
Кредиты будут списаны с вашего баланса после покупки.

"""
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
                        await call.message.answer(text="Please send the picture of product or zip file of images.")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    elif call.data == "batumi_cat":
                        products['prds'][p_id]['category'] = 'batumi'
                        users[userID]['state'] = "waiting_for_product_image"
                        await call.message.answer(text="Please send the picture of product or zip file of images.")
                        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    elif call.data == "kutaisai_cat":
                        products['prds'][p_id]['category'] = 'kutaisai'
                        users[userID]['state'] = "waiting_for_product_image"
                        await call.message.answer(text="Please send the picture of product or zip file of image.")
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
        
                # elif call.data == "wallet":
                    
                #     payments_data ={}
                #     await read_db(payments_data,'payments_data')

                #     if userID in payments_data['payments']:
                #         user_balance = payments_data['payments'][userID]['balance']
                #         if not user_balance == 0:
                #             users[userID]['wallet_balance'] += user_balance
                #             payments_data['payments'][userID]['balance'] =0
                        

                #     res_message = f" Your wallet balance is <b>${users[userID]['wallet_balance']}</b>"
                #     top_up_button =  InlineKeyboardButton(text="TOP UP",callback_data="top_up")
                #     topup_keyboard = InlineKeyboardMarkup().add(top_up_button)
                #     await call.message.answer(text=res_message,reply_markup=topup_keyboard,parse_mode=ParseMode.HTML)

                #     await write_db(payments_data,'payments_data')
                elif call.data == "top_up":

                    res_dict = await create_charge_for_topup(amount=45,userID=userID)

                    qr = qrcode.QRCode(
                        version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4
                    )
                    qr_data = res_dict['receiving_address']
                    qr.add_data(qr_data)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")
                    img_name = f"{res_dict['receiving_address']}_qr.png"
                    img.save(img_name)

                    payment_confirm_button = InlineKeyboardButton(text="✔️Confirm",callback_data="payment_done")
                    payment_keyboard = InlineKeyboardMarkup().add(payment_confirm_button)

                    ltc_rate = float(res_dict['litecoin_rate'])
                    coin_45_amount = round(float(46/ltc_rate),4)
                    coin_80_amount = round(float(81/ltc_rate),4)
                    coin_160_amount = round(float(161/ltc_rate),4)

                    res_message = f"""გადახდის დეტალები / Детали оплаты
<code>{coin_45_amount}</code> Litecoin LTC for <b>$45</b>credit
<code>{coin_80_amount}</code> Litecoin LTC for <b>$80</b>credit
<code>{coin_160_amount}</code> Litecoin LTC for <b>$160</b>credit

<b>Address</b>: <code>{res_dict['receiving_address']}</code>

შეგიძლია გამოაგზავნო ნებისმიერი ოდენობის თანხა / Вы можете отправить любую сумму денег
                
⚠️1 საათში კოდს დრო გაუვა. დააჭირე "შევსება"-ს თავიდან. ბოტი მოგცემს ახალ კოდს. შეეცადე ისე ქნა, რომ ახალი კოდის მოცემისთანავე ჩარიცხო თანხა!

ერთ კოდზე გამოაგზავნე ერთხელ. თუ თანხა დაგაკლდა თავიდან შეავსე ბალანსი.    იგივე კოდზე სადაც უკვე ჩარიცხულიგაქ არ ჩარიცხო!

როცა ჩარიცხავ თანხას დააჭირე "დადასტურება"-ს. დაელოდე 5 - 10 წუთი და თანხა აისახება კრედიტებით. შემდეგ პირდაპირ შეძლებ ბოტისგან მისამართის აღებას.

Срок действия кода истекает через 1 час. Нажмите «Заполнить» еще раз. Бот выдаст вам новый код. Попробуйте внести депозит, как только будет предоставлен новый код!

Внесите сумму один раз за код. Если суммы недостаточно, пополните баланс еще раз. Не вносите деньги на тот же код, на который вы уже вносили депозит!

Когда вы вносите сумму, нажмите «Подтвердить». Подождите 5-10 минут и сумма будет отражена в кредитах. Тогда вы сможете напрямую взять адрес у бота.⚠️"""

                    with open (img_name,'rb') as qrfile:
                        await bot.send_photo(userID,qrfile,caption=res_message,parse_mode=ParseMode.HTML,reply_markup=payment_keyboard)

                    if os.path.exists(img_name):
                        os.remove(img_name)

                elif call.data == "payment_done":
                    res_message = """Please wait for sometime till transaction get confirmed on the network. Once transaction is confirmed you can check your wallet balance by using start command."""
                    await call.message.answer(text=res_message)
                    await bot.edit_message_reply_markup(chat_id=userID,message_id=call.message.message_id,reply_markup=None)
                
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


async def extract_zip_file(zfile_path,output_dir):
    with zipfile.ZipFile(zfile_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)


async def display_edit_products(category,message):
    buttons=[]
    for product in products['prds']:
        if len(products['prds'][product])>=5:
            if products['prds'][product]['category'] == category:
                manage_callback =f'man_{products["prds"][product]["product_id"]}'
                button = InlineKeyboardButton(text=f"{products['prds'][product]['name']}",callback_data=manage_callback)
                buttons.append(button)
    back_button = InlineKeyboardButton(text="⬅️Back",callback_data="back_to_manage_product")
    buttons.append(back_button)
    products_keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await message.reply(text="Select the product from below list which you want to edit.",reply_markup =products_keyboard)



# Get Random Index
async def get_random_index(elem_list):
    random_indices = random.sample(range(len(elem_list)),len(elem_list))
    random_index =random_indices[0]
    return random_index

async def send_picture(userID,p_id):
    if len(products['prds'][p_id]['pictures_name'])>0:
        pictures = products['prds'][p_id]['pictures_name']
        random_index  = await get_random_index(pictures)
        random_picture = pictures[random_index]
        picture_path = f"pictures/{random_picture}"
        if os.path.exists(picture_path):
            with open(picture_path,'rb') as picture:
                await bot.send_photo(chat_id=userID,photo=picture)

        if os.path.exists(picture_path):
            os.remove(picture_path)
        try:
            firebase_storage_path =  firebase_folder_path+random_picture
            blob = bucket.blob(firebase_storage_path)
            blob.delete()
        except Exception as e:
            print(f"Error in deleting from bucket : {e}") 
        products['prds'][p_id]['pictures_name'].remove(random_picture)
    # if p_id in temp_prds:
    #     temp_prds.remove(p_id)
    else:
        await bot.send_message("Product is out of stock,please contact the admin")

    await write_db(products,"products")


async def create_charge(amount, userID, orderID, p_ID):
    url = "https://api.commerce.coinbase.com/charges"
    headers = {
        'X-CC-Api-Key': COINBASE_API,
        'X-CC-Version': '2018-03-22',
        'Content-Type': 'application/json',
    }
    payload = {
        "name": f'{products["prds"][p_ID]["name"]}',
        "description": 'Description',
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



async def create_charge_for_topup(amount, userID ):
    url = "https://api.commerce.coinbase.com/charges"
    headers = {
        'X-CC-Api-Key': COINBASE_API,
        'X-CC-Version': '2018-03-22',
        'Content-Type': 'application/json',
    }
    payload = {
        "name": f'Top Up',
        "description": 'Description',
        "local_price": {
            "amount": amount,
            "currency": "USD",
        },
        "pricing_type": "fixed_price",
        "metadata": {
            'user_id': userID,
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
        response_dict['litecoin_rate'] =  charge['data']['exchange_rates']['LTC-USD']

    return response_dict

async def show_products(category, message):
    buttons = []
    for product in products['prds']:
        if len(products['prds'][product])>=5:
            if products['prds'][product]['category'] == category:
                button = InlineKeyboardButton(
                    text=f'{products["prds"][product]["name"]}', callback_data=f'{products["prds"][product]["product_id"]}')
                buttons.append(button)
    back_button = InlineKeyboardButton(
        text="⬅️Back", callback_data="back_to_main_menu")
    buttons.append(back_button)
    products_keyboard = InlineKeyboardMarkup(row_width=2).add(*buttons)
    await message.reply(text="Select from this list.", reply_markup=products_keyboard)


async def download_images():

    for product in products['prds']:
        if len(products['prds'][product])>=5:
            if len (products['prds'][product]['pictures_name'])>0 :
                try:
                    pictures = products['prds'][product]['pictures_name']
                    for picture in pictures:
                        local_path = f'pictures/{picture}'
                        firebase_storage_path = firebase_folder_path + picture
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

        await asyncio.sleep(600)



async def read_db(wDictonary, dict_name):
    data_ref = db.collection(dict_name)
    data_docs = data_ref.get()

    for doc in data_docs:
        wDictonary[doc.id] = doc.to_dict()




async def main(_):
    await read_db(users, 'users')
    await read_db(products, 'products')
    await download_images()
    asyncio.create_task(webhook_hitter())


    print("Bot is started..")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=main)
