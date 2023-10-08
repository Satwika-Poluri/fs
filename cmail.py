import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',587)
    server.login('satwikapoluri@gmail.com','rpcg owoh nkij fmgm')
    msg=EmailMessage()
    msg['From']= 'satwikapoluri@gmail.com'
    msg['To']=to
    msg['Subject']=subject
    msg.set_content(body)
    server.send_message(msg)
    server.quit()